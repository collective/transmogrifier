# -*- coding: utf-8 -*-
"""
Usage: transmogrify <pipeline>...
                    [--overrides=<path/to/pipeline/overrides.cfg>]
                    [--context=<path.to.context.factory>]
       transmogrify --list
"""
import os
import importlib
import logging

from docopt import docopt
from zope.component import getUtilitiesFor
from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationMachine
from zope.configuration.xmlconfig import registerCommonDirectives

from six import print_
from six import text_type as u
from six.moves import configparser

from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.interfaces import ITransmogrifier
from transmogrifier.registry import configuration_registry


try:
    import venusianconfiguration
    HAS_VENUSIANCONFIGURATION = True
except ImportError:
    venusianconfiguration = None
    HAS_VENUSIANCONFIGURATION = False


def __main__():
    # Enable logging
    logging.basicConfig(level=logging.INFO)

    # Parse cli arguments
    arguments = docopt(__doc__)

    # Enable venuasianconfiguration
    if HAS_VENUSIANCONFIGURATION:
        venusianconfiguration.enable()

    # Parse and evaluate configuration and plugins
    config = ConfigurationMachine()
    registerCommonDirectives(config)

    import transmogrifier
    xmlconfig.include(config, package=transmogrifier, file='meta.zcml')
    xmlconfig.include(config, package=transmogrifier, file='configure.zcml')

    config.execute_actions()

    if arguments.get('--list'):
        blueprints = dict(getUtilitiesFor(ISectionBlueprint))
        pipelines = map(configuration_registry.getConfiguration,
                        configuration_registry.listConfigurationIds())
        print_("""
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

    # Load optional overrides
    overrides = {}
    overrides_path = arguments.get('--overrides')
    if overrides_path and not os.path.isabs(overrides_path):
        overrides_path = os.path.join(os.getcwd(), overrides_path)
    if overrides_path:
        parser = configparser.RawConfigParser()
        parser.optionxform = str  # case sensitive
        with open(overrides_path) as fp:
            parser.readfp(fp)
        overrides.update(dict(((section, dict(parser.items(section)))
                               for section in parser.sections())))

    # Initialize optional context
    context_path = arguments.get('--context')
    if context_path is None:
        context = dict()
    else:
        context_module_path, context_class_name = context_path.rsplit('.', 1)
        context_module = importlib.import_module(context_module_path)
        context = getattr(context_module, context_class_name)()

    # Transmogrify
    for pipeline in arguments.get('<pipeline>'):
        try:
            ITransmogrifier(context)(pipeline, **overrides)
        except KeyError:
            path = (os.path.isabs(pipeline) and pipeline
                    or os.path.join(os.getcwd(), pipeline))
            if os.path.isfile(path):
                configuration_registry.registerConfiguration(
                    name=u(pipeline), title=u(pipeline),
                    description=u('n/a'), configuration=path)
                ITransmogrifier(context)(pipeline, **overrides)
            else:
                raise
