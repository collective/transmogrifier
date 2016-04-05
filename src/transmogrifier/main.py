# -*- coding: utf-8 -*-
"""
Usage: transmogrify <pipelines_and_overrides>...
                    [--overrides=overrides.cfg>]
                    [--include=package_or_module>...]
                    [--include=package:filename>...]
                    [--context=<package.module.factory>]
       transmogrify --list
                    [--include=package_or_module>...]
       transmogrify --show=<pipeline>
                    [--include=package_or_module>...]
"""
from __future__ import unicode_literals
from __future__ import print_function
from contextlib import contextmanager
from operator import add
from functools import reduce

import os
import importlib
import logging
import sys

from docopt import docopt
from future.moves.collections import OrderedDict
from six import BytesIO
from zope.component import getUtilitiesFor
from zope.component.hooks import getSite
from zope.component.hooks import setSite
from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationMachine
from zope.configuration.xmlconfig import registerCommonDirectives

from configparser import RawConfigParser

from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.interfaces import ITransmogrifier
from transmogrifier.registry import configuration_registry
from transmogrifier.utils import load_config
from transmogrifier.utils import get_lines

from pkg_resources import get_distribution
from pkg_resources import DistributionNotFound
from pkg_resources import resource_exists

try:
    get_distribution('venusianconfiguration')
except DistributionNotFound:
    HAS_VENUSIANCONFIGURATION = False
else:
    HAS_VENUSIANCONFIGURATION = True

try:
    get_distribution('Zope2')
except DistributionNotFound:
    HAS_ZOPE = False
else:
    HAS_ZOPE = True


def get_argv():
    argv = sys.argv[:]
    for i in range(len(sys.argv)):
        # Support execution as an argument for some wrapper script
        # e.g. bin/instance -OPlone bin/transmogrify pipeline.cfg
        if os.path.basename(sys.argv[i]) == 'transmogrify':
            argv = sys.argv[i:]
            break
    return argv


def parse_override(s):
    section, override = s.split(':', 1)
    name, value = override.split('=', 1)
    return section, name, value


def get_overrides(arguments):
    overrides = {}

    overrides_path = arguments.get('--overrides')
    if overrides_path and not os.path.isabs(overrides_path):
        overrides_path = os.path.join(os.getcwd(), overrides_path)
    if overrides_path:
        parser = RawConfigParser()
        parser.optionxform = str  # case sensitive
        with open(overrides_path) as fp:
            parser.readfp(fp)
        overrides.update(dict(((section, dict(parser.items(section)))
                               for section in parser.sections())))

    for candidate in arguments.get('<pipelines_and_overrides>'):
        try:
            section, name, value = parse_override(candidate)
        except ValueError:
            continue
        overrides.setdefault(section, {})
        overrides[section][name] = value

    return overrides


def get_pipelines(arguments):
    for candidate in arguments.get('<pipelines_and_overrides>'):
        try:
            parse_override(candidate)
        except ValueError:
            yield candidate


def parse_include(spec):
    cleanup = False
    if '.' not in sys.path:
        sys.path.append('.')
        cleanup = True
    try:
        package, filename = spec.split(':', 1)
    except ValueError:
        package = spec
        filename = None
    if not filename and resource_exists(package, 'configure.zcml'):
        filename = 'configure.zcml'
    elif HAS_VENUSIANCONFIGURATION:
        if not filename and resource_exists(package, 'configure.py'):
            filename = 'configure.py'
        else:
            # Support including single module in the current working directory
            package = importlib.import_module(package)
    if cleanup:
        sys.path.remove('.')
    return package, filename


def configure(arguments):
    # Enable venuasianconfiguration
    if HAS_VENUSIANCONFIGURATION:
        import venusianconfiguration
        venusianconfiguration.enable()

    # BBB: Support Zope's global configuration context
    if HAS_ZOPE:
        try:
            import Zope2.App.zcml
            config = Zope2.App.zcml._context or ConfigurationMachine()
        except (ImportError, AttributeError):
            config = ConfigurationMachine()
    else:
        config = ConfigurationMachine()

    # Parse and evaluate configuration and plugins
    registerCommonDirectives(config)

    import transmogrifier
    xmlconfig.include(config, package=transmogrifier, file='meta.zcml')
    xmlconfig.include(config, package=transmogrifier, file='configure.zcml')

    # Resolve includes
    for include in set(arguments.get('--include')):
        package, filename = parse_include(include)
        if package and filename:
            package = importlib.import_module(package)
            xmlconfig.include(config, package=package, file=filename)
        elif package and HAS_VENUSIANCONFIGURATION:
            # Support including single module in the current working directory
            import venusianconfiguration
            venusianconfiguration.venusianscan(package, config)

    config.execute_actions()


def resolve(pipeline):
    config = load_config(pipeline)
    resolved = RawConfigParser(dict_type=OrderedDict)
    resolved.add_section('transmogrifier')
    for key in sorted(config.get('transmogrifier')):
        resolved.set('transmogrifier', key, config['transmogrifier'][key])
    sections = reduce(
        add, [get_lines(config.get(section).get('pipeline') or '')
              for section in config.keys()])
    for section in sorted(config.keys()):
        if section not in sections or section in resolved.sections():
            continue
        resolved.add_section(section)
        for key in sorted(config.get(section)):
            resolved.set(section, key, config[section][key])
    return resolved


@contextmanager
def global_site_manager():
    site = getSite()
    if site is not None:
        setSite()
    yield
    if site is not None:
        setSite(site)


def __main__():
    # Enable logging
    logging.basicConfig(level=logging.INFO)

    # Parse cli arguments
    arguments = docopt(__doc__, argv=get_argv()[1:])

    # Resolve configuration
    with global_site_manager():
        configure(arguments)

    # Show registered components
    if arguments.get('--list'):
        blueprints = dict(getUtilitiesFor(ISectionBlueprint))
        pipelines = map(configuration_registry.getConfiguration,
                        configuration_registry.listConfigurationIds())
        print("""
Available blueprints
--------------------
{0:s}

Available pipelines
-------------------
{1:s}
""".format('\n'.join(sorted(blueprints.keys())),
           '\n'.join(['{0:s}\n    {1:s}: {2:s}'.format(
                      p['id'], p['title'], p['description'])
                      for p in pipelines])))
        return

    # Show specified configuration
    if arguments.get('--show'):
        pipeline = arguments.get('--show')
        try:
            configuration_registry.getConfiguration(pipeline)
        except KeyError:
            path = (os.path.isabs(pipeline) and pipeline or
                    os.path.join(os.getcwd(), pipeline))
            if os.path.isfile(path):
                configuration_registry.registerConfiguration(
                    name=pipeline, title=pipeline,
                    description='n/a', configuration=path)
            else:
                raise

        output = BytesIO()
        resolve(pipeline).write(output)
        print(output.getvalue())

        return

    # Load optional overrides
    overrides = get_overrides(arguments)

    # Initialize optional context
    context_path = arguments.get('--context')
    if context_path is None:
        context = dict()
    else:
        context_module_path, context_class_name = context_path.rsplit('.', 1)
        context_module = importlib.import_module(context_module_path)
        context = getattr(context_module, context_class_name)()

    # Transmogrify
    for pipeline in get_pipelines(arguments):
        path = (os.path.isabs(pipeline) and pipeline or
                os.path.join(os.getcwd(), pipeline))
        if os.path.isfile(path):
            configuration_registry.registerConfiguration(
                name=pipeline, title=pipeline,
                description='n/a', configuration=path)
        ITransmogrifier(context)(pipeline, **overrides)
