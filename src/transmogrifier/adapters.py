# -*- coding: utf-8 -*-
from zope.component import adapter

from zope.interface import implementer
from zope.interface import Interface

from six.moves import UserDict

from transmogrifier.interfaces import ITransmogrifier
from transmogrifier.options import Options
from transmogrifier.utils import load_config
from transmogrifier.utils import constructPipeline


@implementer(ITransmogrifier)
@adapter(Interface)
class Transmogrifier(UserDict):

    def __init__(self, context):
        self.context = context

    def __call__(self, configuration_id, **overrides):
        self.configuration_id = configuration_id
        self._raw = load_config(configuration_id, **overrides)
        self._data = {}

        options = self._raw['transmogrifier']
        sections = options['pipeline'].splitlines()
        pipeline = constructPipeline(self, sections)

        # Pipeline execution
        for item in pipeline:
            pass  # discard once processed

    def __getitem__(self, section):
        try:
            return self._data[section]
        except KeyError:
            pass

        # May raise key error
        data = self._raw[section]

        options = Options(self, section, data)
        self._data[section] = options
        options.substitute()
        return options

    def __setitem__(self, key, value):
        raise NotImplementedError('__setitem__')

    def __delitem__(self, key):
        raise NotImplementedError('__delitem__')

    def keys(self):
        return self._raw.keys()

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        for k in self.keys():
            yield k
