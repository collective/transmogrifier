# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from zope.component import getUtility

from transmogrifier.blueprints import ConditionalBlueprint
from transmogrifier.interfaces import ISection
from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.utils import get_lines


class Buffer(object):

    def __init__(self):
        self.data = []

    def insert(self, item):
        self.data.insert(0, item)

    def __iter__(self):
        while self.data:
            yield self.data.pop()


class Pipeline(ConditionalBlueprint):
    def __iter__(self):
        sections = get_lines(self.options.get('pipeline'))
        items = Buffer()
        pipeline = []

        for section_id in sections:
            if not section_id or section_id == self.name:
                continue

            blueprint_id = self.transmogrifier[section_id]['blueprint']
            blueprint = getUtility(ISectionBlueprint, blueprint_id)

            if not pipeline:
                pipeline = blueprint(self.transmogrifier, section_id,
                                     self.transmogrifier[section_id], items)
            else:
                pipeline = blueprint(self.transmogrifier, section_id,
                                     self.transmogrifier[section_id], pipeline)

            if not ISection.providedBy(pipeline):
                raise ValueError('Blueprint %s for section %s did not return '
                                 'an ISection' % (blueprint_id, section_id))

        iterated = False

        for item in self.previous:
            if pipeline and self.condition(item):
                items.insert(item)
                for sub_item in iter(pipeline):
                    yield sub_item
                iterated = True
            else:
                yield item

        # Executed non-iterated sections to support source blueprints
        if not iterated:
            for item in iter(pipeline):
                yield item
