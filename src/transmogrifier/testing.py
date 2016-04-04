# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import shutil
import tempfile

from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationMachine
from zope.configuration.xmlconfig import registerCommonDirectives

from transmogrifier.registry import configuration_registry

try:
    from zope.testing.cleanup import cleanUp
except ImportError:
    def cleanUp():
        pass


# noinspection PyPep8Naming
class TransmogrifierLayer(object):

    tempdir = None
    context = None

    @classmethod
    def setUp(cls):
        pass

    @classmethod
    def tearDown(cls):
        pass

    # noinspection PyUnusedLocal
    @classmethod
    def testSetUp(cls, test=None):
        cls.context = ConfigurationMachine()
        registerCommonDirectives(cls.context)

        import transmogrifier
        xmlconfig.file('meta.zcml', transmogrifier, context=cls.context)
        xmlconfig.file('configure.zcml', transmogrifier, context=cls.context)

        cls.tempdir = tempfile.mkdtemp('transmogrifierTestConfigs')

    # noinspection PyUnusedLocal
    @classmethod
    def testTearDown(cls, test=None):
        shutil.rmtree(cls.tempdir)
        cleanUp()

    @classmethod
    def registerConfiguration(cls, name, configuration):
        filename = os.path.join(cls.tempdir, '{0:s}.cfg'.format(name))
        with open(filename, 'w') as fp:
            fp.write(configuration)
        configuration_registry.registerConfiguration(
            name=name,
            title="Pipeline configuration '{0:s}' from "
                  "'transmogrifier.tests'".format(name),
            description='',
            configuration=filename
        )
