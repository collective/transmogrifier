# -*- coding: utf-8 -*-
"""Usage: transmogrify <pipeline>
                    [--overrides=<path/to/pipeline/overrides.cfg>]
                    [--context=<path.to.context.factory>]
"""
import os
import ConfigParser
import importlib
import logging

from docopt import docopt
from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationMachine
from zope.configuration.xmlconfig import registerCommonDirectives

import collective.transmogrifier
from collective.transmogrifier.interfaces import ITransmogrifier


class DefaultContext(object):
    """Default transmogrifier context"""


def __main__():
    # Enable logging
    logging.basicConfig(level=logging.INFO)

    # Parse cli arguments
    arguments = docopt(__doc__)

    # Parse and evaluate configuration and plugins
    config = ConfigurationMachine()
    registerCommonDirectives(config)
    xmlconfig.include(config, package=collective.transmogrifier,
                      file='meta.zcml')
    xmlconfig.include(config, package=collective.transmogrifier,
                      file='configure.zcml')
    config.execute_actions()

    # Load optional overrides
    overrides = {}
    overrides_path = arguments.get('--overrides')
    if overrides_path and not os.path.isabs(overrides_path):
        overrides_path = os.path.join(os.getcwd(), overrides_path)
    if overrides_path:
        parser = ConfigParser.RawConfigParser()
        parser.optionxform = str  # case sensitive
        with open(overrides_path) as fp:
            parser.readfp(fp)
        overrides.update(dict(((section, dict(parser.items(section)))
                               for section in parser.sections())))

    # Initialize optional context
    context_path = arguments.get('--context')
    if context_path is None:
        context = DefaultContext
    else:
        context_module_path, context_class_name = context_path.rsplit('.', 1)
        context_module = importlib.import_module(context_module_path)
        context = getattr(context_module, context_class_name)()

    # Transmogrify
    ITransmogrifier(context)(arguments.get('<pipeline>'), **overrides)
