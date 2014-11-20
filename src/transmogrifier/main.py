# -*- coding: utf-8 -*-
"""
Usage: transmogrify <pipelines_and_overrides>...
                    [--overrides=<path/to/pipeline/overrides.cfg>]
                    [--context=<path.to.context.factory>]
       transmogrify --list
       transmogrify --show=<pipeline>
"""
from __future__ import unicode_literals
from __future__ import print_function

import os
import importlib
import logging
import sys

from docopt import docopt
from zope.component import getUtilitiesFor
from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationMachine
from zope.configuration.xmlconfig import registerCommonDirectives

from configparser import RawConfigParser

from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.interfaces import ITransmogrifier
from transmogrifier.registry import configuration_registry

import pkg_resources

try:
    pkg_resources.get_distribution('venusianconfiguration')
except pkg_resources.DistributionNotFound:
    HAS_VENUSIANCONFIGURATION = False
else:
    HAS_VENUSIANCONFIGURATION = True

try:
    pkg_resources.get_distribution('Zope2')
except pkg_resources.DistributionNotFound:
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


def configure():
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
    config.execute_actions()


def __main__():
    # Enable logging
    logging.basicConfig(level=logging.INFO)

    # Parse cli arguments
    arguments = docopt(__doc__, argv=get_argv()[1:])

    # Resolve configuration
    configure()

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
            filename = configuration_registry.getConfiguration(
                pipeline)['configuration']
        except KeyError:
            path = (os.path.isabs(pipeline) and pipeline
                    or os.path.join(os.getcwd(), pipeline))
            if os.path.isfile(path):
                filename = path
            else:
                raise
        with open(filename, 'r') as fp:
            print(fp.read())
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
        try:
            ITransmogrifier(context)(pipeline, **overrides)
        except KeyError:
            path = (os.path.isabs(pipeline) and pipeline
                    or os.path.join(os.getcwd(), pipeline))
            if os.path.isfile(path):
                configuration_registry.registerConfiguration(
                    name=pipeline, title=pipeline,
                    description='n/a', configuration=path)
                ITransmogrifier(context)(pipeline, **overrides)
            else:
                raise
