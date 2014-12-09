# -*- coding: utf-8 -*-
from zope.component import adapter

from zope.interface import implementer
from zope.interface import Interface

from future.moves.collections import UserDict

from transmogrifier.interfaces import ITransmogrifier
from transmogrifier.options import Options
from transmogrifier.utils import load_config
from transmogrifier.utils import constructPipeline


@implementer(ITransmogrifier)
@adapter(Interface)
class Transmogrifier(UserDict):

    def __init__(self, context):
        self.context = context
        self._data = {}
        self.data = {}

    def __call__(self, configuration_id, **overrides):
        self.configuration_id = configuration_id
        self._data = load_config(configuration_id, **overrides)
        self.data = {}

        options = self._data['transmogrifier']
        sections = options['pipeline'].splitlines()
        pipeline = constructPipeline(self, sections)

        # Pipeline execution
        for item in pipeline:
            pass  # discard once processed

    def __getitem__(self, section):
        try:
            return self.data[section]
        except KeyError:
            pass

        # May raise key error
        data = self._data[section]

        options = Options(self, section, data)
        self[section] = options  # must be set before substitution below
        options.substitute()

        return self.data[section]

    def keys(self):
        return self._data.keys()

    def has_key(self, key):
        return key in self.keys()

    def iterkeys(self):
        for key in self.keys():
            yield key

    def items(self):
        for key in self.keys():
            yield key, self[key]

    iteritems = items

    def values(self):
        for key in self.keys():
            yield self[key]

    itervalues = values

    def __len__(self):
        return len(list(self.keys()))

    def __iter__(self):
        for k in self.keys():
            yield k

    def __contains__(self, key):
        return key in self.keys()
