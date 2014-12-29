# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

import os
import unittest
import operator
import doctest

from transmogrifier import Transmogrifier

from transmogrifier.blueprints import Blueprint
from zope.interface import classImplements
from zope.component import provideUtility
from zope.configuration import xmlconfig
from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.interfaces import ISection
from transmogrifier.registry import configuration_registry
from transmogrifier.testing import TransmogrifierLayer
from zope.testing.loggingsupport import InstalledHandler


class MetaDirectivesTests(unittest.TestCase):

    layer = TransmogrifierLayer

    def testEmptyZCML(self):
        xmlconfig.string("""\
<configure xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier">
</configure>""", context=self.layer.context)
        self.layer.context.execute_actions()
        self.assertEqual(configuration_registry.listConfigurationIds(), ())

    def testConfigZCML(self):
        xmlconfig.string("""\
<configure
    xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier"
    i18n_domain="transmogrifier">
  <transmogrifier:pipeline
      name="transmogrifier.tests.configname"
      title="config title"
      description="config description"
      configuration="filename.cfg"
      />
</configure>""", context=self.layer.context)
        self.layer.context.execute_actions()

        self.assertEqual(configuration_registry.listConfigurationIds(),
                         ('transmogrifier.tests.configname',))
        self.assertEqual(
            configuration_registry.getConfiguration(
                'transmogrifier.tests.configname'),
            dict(id='transmogrifier.tests.configname',
                 title='config title',
                 description='config description',
                 configuration=os.path.join(os.getcwd(), 'filename.cfg')))

    def testConfigZCMLDefaults(self):
        xmlconfig.string("""\
<configure
    xmlns:transmogrifier="http://namespaces.plone.org/transmogrifier"
    i18n_domain="transmogrifier">
  <transmogrifier:pipeline
      name="transmogrifier.tests.configname"
      configuration="filename.cfg"
      />
</configure>""", context=self.layer.context)
        self.layer.context.execute_actions()
        self.assertEqual(configuration_registry.listConfigurationIds(),
                         ('transmogrifier.tests.configname',))
        self.assertEqual(
            configuration_registry.getConfiguration(
                'transmogrifier.tests.configname'),
            dict(id='transmogrifier.tests.configname',
                 title='Pipeline configuration '
                       "'transmogrifier.tests.configname'",
                 description='',
                 configuration=os.path.join(os.getcwd(), 'filename.cfg')))


class OptionSubstitutionTests(unittest.TestCase):

    layer = TransmogrifierLayer

    def _loadOptions(self, opts):
        from transmogrifier.adapters import Transmogrifier
        tm = Transmogrifier({})
        tm._data = opts
        return tm

    def testNoSubs(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='python'),
                eggs=dict(foo='bar'),
            ))
        self.assertEqual(opts['spam']['monty'], 'python')
        self.assertEqual(opts['eggs']['foo'], 'bar')

    def testSimpleSub(self):
        opts = self._loadOptions(dict(
            spam=dict(monty='python'),
            eggs=dict(foo='${spam:monty}'),
        ))
        self.assertEqual(opts['spam']['monty'], 'python')
        self.assertEqual(opts['eggs']['foo'], 'python')

    def testSkipTALESStringExpressions(self):
        opts = self._loadOptions(
            dict(
                spam=dict(monty='string:${spam/eggs}'),
                eggs=dict(foo='${spam/monty}')
            ))
        self.assertEqual(opts['spam']['monty'], 'string:${spam/eggs}')
        self.assertRaises(ValueError, operator.itemgetter('eggs'), opts)

    def testErrors(self):
        opts = self._loadOptions(
            dict(
                empty=dict(),
                spam=dict(monty='${eggs:foo}'),
                eggs=dict(foo='${spam:monty}'),
            ))
        self.assertRaises(ValueError, operator.itemgetter('spam'), opts)
        self.assertRaises(KeyError, operator.itemgetter('do_not_exist'), opts)
        self.assertRaises(KeyError, operator.itemgetter('do_not_exist'),
                          opts['empty'])


class InclusionManipulationTests(unittest.TestCase):

    layer = TransmogrifierLayer

    def setUp(self):
        self.layer.registerConfiguration(
            'transmogrifier.tests.included',
            """\
[foo]
bar =
    monty
    python
""")

    def _loadConfig(self, config):
        from transmogrifier.utils import load_config
        full_config = """\
[transmogrifier]
include=transmogrifier.tests.included
""" + config
        self.layer.registerConfiguration('transmogrifier.tests.includer',
                                         full_config)
        return load_config('transmogrifier.tests.includer')

    def testAdd(self):
        opts = self._loadConfig('[foo]\nbar+=eggs\n')
        self.assertEquals(opts['foo']['bar'], 'monty\npython\neggs')

    def testRemove(self):
        opts = self._loadConfig('[foo]\nbar-=python\n')
        self.assertEquals(opts['foo']['bar'], 'monty')

    def testAddAndRemove(self):
        opts = self._loadConfig("""\
[foo]
bar -=
    monty
bar +=
    monty
    eggs
""")
        self.assertEquals(opts['foo']['bar'], 'python\nmonty\neggs')

    def testNonExistent(self):
        opts = self._loadConfig('[bar]\nfoo+=spam\nbaz-=monty\n')
        self.assertEquals(opts['bar']['foo'], 'spam')
        self.assertEquals(opts['bar']['baz'], '')


class ConstructPipelineTests(unittest.TestCase):

    layer = TransmogrifierLayer

    def _doConstruct(self, transmogrifier, sections, pipeline=None):
        from transmogrifier.utils import constructPipeline
        return constructPipeline(transmogrifier, sections, pipeline)

    def testNoISection(self):
        config = dict(
            noisection=dict(
                blueprint='transmogrifier.tests.noisection'))

        class NotAnISection(object):
            def __init__(self, transmogrifier, name, options, previous):
                self.previous = previous

            def __iter__(self):
                for item in self.previous:
                    yield item

        provideUtility(NotAnISection, ISectionBlueprint,
                       name='transmogrifier.tests.noisection')
        self.assertRaises(ValueError, self._doConstruct,
                          config, ['noisection'])

        classImplements(NotAnISection, ISection)
        # No longer raises
        self._doConstruct(config, ['noisection'])


class DefaultKeysTest(unittest.TestCase):

    layer = TransmogrifierLayer

    def _defaultKeys(self, *args):
        from transmogrifier.utils import defaultKeys
        return defaultKeys(*args)

    def testWithKey(self):
        self.assertEqual(
            self._defaultKeys('foo.bar.baz', 'spam', 'eggs'),
            ('_foo.bar.baz_spam_eggs', '_foo.bar.baz_eggs',
             '_spam_eggs', '_eggs'))

    def testWithoutKey(self):
        self.assertEqual(
            self._defaultKeys('foo.bar.baz', 'spam'),
            ('_foo.bar.baz_spam', '_foo.bar.baz', '_spam'))


class PackageReferenceResolverTest(unittest.TestCase):

    layer = TransmogrifierLayer

    def setUp(self):
        self._package_path = os.path.dirname(__file__)[:-len('/tests')]

    def _resolvePackageReference(self, ref):
        from transmogrifier.utils import resolvePackageReference
        return resolvePackageReference(ref)

    def testPackageResolver(self):
        res = self._resolvePackageReference('transmogrifier:test')
        self.assertEqual(res, os.path.join(self._package_path, 'test'))

    def testNonExistingPackage(self):
        self.assertRaises(ImportError, self._resolvePackageReference,
                          'transmogrifier.nonexistent:test')


def test_suite():
    import sys
    suite = unittest.findTestCases(sys.modules[__name__])
    suite.addTests((
        doctest.DocFileSuite(
            '../../../docs/transmogrifier.rst',
            '../../../docs/blueprints/logger.rst',
            '../../../docs/blueprints/breakpoint.rst',
            setUp=TransmogrifierLayer.testSetUp,
            tearDown=TransmogrifierLayer.testTearDown,
            globs={'registerConfiguration':
                   TransmogrifierLayer.registerConfiguration,
                   'Transmogrifier': Transmogrifier({}),
                   'logger': InstalledHandler('logger', level=logging.DEBUG)},
            optionflags=doctest.NORMALIZE_WHITESPACE),
    ))
    return suite
