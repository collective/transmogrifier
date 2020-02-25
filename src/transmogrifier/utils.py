# -*- coding: utf-8 -*-
from operator import methodcaller
import os.path
import re
import pprint

from six import iteritems
from six import StringIO
from zope.component import getUtility

from configparser import RawConfigParser
from zope.interface.common.mapping import IMapping
from zope.interface.exceptions import BrokenImplementation
from zope.interface.verify import verifyObject
from transmogrifier.interfaces import ISection
from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.registry import configuration_registry


def pformat_msg(obj):
    fp = StringIO()
    pprint.pprint(obj, fp)
    return fp.getvalue()


def to_boolean(value):
    return str(value).lower() in ['1', 'true', 'on', 'yes', 'enabled']


def is_mapping(item):
    """Validate that item can acts as a mapping
    """
    try:
        verifyObject(IMapping, item, tentative=True)
    except BrokenImplementation as e:
        # Allow mapping to miss __iter__ to support email.message.Message
        if e.name not in ['__iter__']:
            raise
    return True


def get_words(value):
    """Return non-zero whitespace separated parts"""
    return list(filter(bool, map(methodcaller('strip'),
                                 (value or '').split())))


def get_lines(value):
    """Return non-zero new line separated parts"""
    return list(filter(bool, map(methodcaller('strip'),
                                 (value or '').splitlines())))


def resolvePackageReference(reference):
    """Given a package:filename reference, return the filesystem path

    ``package`` is a dotted name to a python package, ``filename`` is assumed
    to be a filename located within the package directory.

    """
    package, filename = reference.strip().split(':', 1)
    package = __import__(package, {}, {}, ('*',))
    return os.path.join(os.path.dirname(package.__file__), filename)


def constructPipeline(transmogrifier, sections, pipeline=None):
    """Construct a transmogrifier pipeline

    ``sections`` is a list of pipeline section ids. Start the pipeline with
    ``pipeline``, or if that's None, with an empty iterator.

    """
    if pipeline is None:
        pipeline = iter(())  # empty starter section

    for section_id in sections:
        section_options = transmogrifier[section_id]
        blueprint_id = section_options['blueprint']
        blueprint = getUtility(ISectionBlueprint, blueprint_id)
        pipeline = blueprint(transmogrifier, section_id,
                             section_options, pipeline)
        if not ISection.providedBy(pipeline):
            raise ValueError('Blueprint %s for section %s did not return '
                             'an ISection' % (blueprint_id, section_id))
        pipeline = iter(pipeline)  # ensure you can call .next()

    return pipeline


def defaultKeys(blueprint, section, key=None):
    """Create a set of item keys based on blueprint id, section name and key

    These keys will match more specifically targeted item keys first; first
    _blueprint_section_key, then _blueprint_key, then _section_key, then _key.

    key is optional, and when omitted results in _blueprint_section, then
    _blueprint, then _section

    """
    parts = ['', blueprint, section]
    if key is not None:
        parts.append(key)
    keys = (
        '_'.join(parts),  # _blueprint_section_key or _blueprint_section
        '_'.join(parts[:2] + parts[3:]),  # _blueprint_key or _blueprint
        '_'.join(parts[:1] + parts[2:]),  # _section_key or _section
    )
    if key is not None:
        keys += ('_'.join(parts[:1] + parts[3:]),)  # _key
    return keys


def defaultMatcher(options, option_name, section, key=None, extra=()):
    """Create a Matcher from an option, with a defaultKeys fallback

    If option_name is present in options, that option is used to create a
    Matcher, with the assumption the option holds newline-separated keys.

    Otherwise, defaultKeys is called to generate a default set of keys
    based on options['blueprint'], section and the optional key. Any
    keys in extra are also considered part of the default keys.

    """
    if option_name in options:
        keys = get_lines(options[option_name])
    else:
        keys = defaultKeys(options['blueprint'], section, key)
        for key in extra:
            keys += (key,)
    return Matcher(*keys)


class Matcher(object):
    """Given a set of string expressions, return the first match.

    Normally items are matched using equality, unless the expression
    starts with re: or regexp:, in which case it is treated as a regular
    expression.

    Regular expressions will be compiled and applied in match mode
    (matching anywhere in the string).

    On calling, returns a tuple of (matched, matchresult), where matched is
    the matched value, and matchresult is either a boolean or the regular
    expression match object. When no match was made, (None, False) is
    returned.

    """
    def __init__(self, *expressions):
        self.expressions = []
        for expr in expressions:
            expr = expr.strip()
            if not expr:
                continue
            if expr.startswith('re:') or expr.startswith('regexp:'):
                expr = expr.split(':', 1)[1]
                expr = re.compile(expr).match
            else:
                expr = lambda x, y=expr: x == y  # noqa
            self.expressions.append(expr)

    def __call__(self, *values):
        for expr in self.expressions:
            for value in values:
                match = expr(value)
                if match:
                    return value, match
        return None, False


def load_config(configuration_id, seen=None, **overrides):  # flake8: noqa
    if seen is None:
        seen = []
    if configuration_id in seen:
        raise ValueError(
            'Recursive configuration extends: %s (%r)' % (configuration_id,
                                                          seen))
    seen.append(configuration_id)

    if ':' in configuration_id:
        configuration_file = resolvePackageReference(configuration_id)
    else:
        config_info = configuration_registry.getConfiguration(configuration_id)
        configuration_file = config_info['configuration']

    parser = RawConfigParser()
    parser.optionxform = str  # case sensitive
    parser.readfp(open(configuration_file))

    result = {}
    includes = None
    for section in parser.sections():
        result[section] = dict(parser.items(section))
        if section == 'transmogrifier':
            includes = result[section].pop('include', includes)

    if includes:
        for configuration_id in includes.split()[::-1]:
            include = load_config(configuration_id, seen)
            sections = set(include.keys()) | set(result.keys())
            for section in sections:
                result[section] = update_section(
                    result.get(section, {}), include.get(section, {}))

    seen.pop()

    for section, options in iteritems(overrides):
        assert section in result, \
            'Overrides include non-existing section {0:s}'.format(section)
        for key, value in iteritems(options):
            assert key in result[section], \
                'Overrides include non-existing key {0:s}:{1:s}'.format(
                    section, key)
            result[section][key] = value

    return result


def update_section(section, included):
    """Update section dictionary with included options

    Included options are only put into the section if not already defined.
    Section keys ending with + or - are the sum or difference respectively
    of that option and the included options. Note that - options are processed
    before + options.

    """
    keys = set(section.keys())
    add = set([k for k in keys if k.endswith('+')])
    remove = set([k for k in keys if k.endswith('-')])

    for key in remove:
        option = key.strip(' -')
        if option in keys:
            raise ValueError('Option %s specified twice', option)
        included[option] = '\n'.join([
            v for v in get_lines(included.get(option))
            if v not in get_lines(section[key])])
        del section[key]

    for key in add:
        option = key.strip(' +')
        if option in keys:
            raise ValueError('Option %s specified twice', option)
        included[option] = '\n'.join([
            v for v in
            get_lines(included.get(option)) + get_lines(section[key])
        ])
        del section[key]

    included.update(section)
    return included
