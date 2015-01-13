# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from zope.component import getUtility

from transmogrifier.blueprints import ConditionalBlueprint
from transmogrifier.interfaces import ISection
from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.utils import get_lines


class SectionWrapper(object):

    def __init__(self, section):
        self.section = section
        self.skipped = []

    def purge(self):
        while self.skipped:
            yield self.skipped.pop()

    def __iter__(self):
        for item in self.section.previous:
            if self.section.condition(item):
                yield item
            else:
                self.skipped.insert(0, item)


class Pipeline(ConditionalBlueprint):
    def __iter__(self):
        sections = get_lines(self.options.get('pipeline'))
        wrapper = SectionWrapper(self)
        pipeline = []

        for section_id in sections:
            if not section_id or section_id == self.name:
                continue

            blueprint_id = self.transmogrifier[section_id]['blueprint']
            blueprint = getUtility(ISectionBlueprint, blueprint_id)

            if not pipeline:
                pipeline = blueprint(self.transmogrifier, section_id,
                                     self.transmogrifier[section_id], wrapper)
            else:
                pipeline = blueprint(self.transmogrifier, section_id,
                                     self.transmogrifier[section_id], pipeline)

            if not ISection.providedBy(pipeline):
                raise ValueError('Blueprint %s for section %s did not return '
                                 'an ISection' % (blueprint_id, section_id))

        pipeline = iter(pipeline)

        try:
            while True:
                item = next(pipeline)
                for skipped in wrapper.purge():
                    yield skipped
                yield item
        except StopIteration:
            for skipped in wrapper.purge():
                yield skipped

        for item in self.previous:
            yield item
