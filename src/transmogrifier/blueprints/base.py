# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from zope.interface import provider
from zope.interface import implementer

from transmogrifier.condition import Condition

from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.interfaces import ISection


@provider(ISectionBlueprint)
@implementer(ISection)
class Blueprint(object):

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous

    def __iter__(self):
        raise NotImplementedError('__iter__')


@provider(ISectionBlueprint)
@implementer(ISection)
class ConditionalBlueprint(Blueprint):

    def __init__(self, transmogrifier, name, options, previous):
        super(ConditionalBlueprint, self).__init__(
            transmogrifier, name, options, previous)

        self.condition = Condition(
            options.get('condition', 'python:True'),
            transmogrifier, name, options
        )

    def __iter__(self):
        raise NotImplementedError('__iter__')
