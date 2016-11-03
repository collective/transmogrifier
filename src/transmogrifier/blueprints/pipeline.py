# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from zope.component import getUtility

from transmogrifier.blueprints import Blueprint
from transmogrifier.interfaces import ISection
from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.utils import get_lines


class Pipeline(Blueprint):
    """Pipeline blueprint works as composition blueprint or (as empty)
    as an extension slot for re-usable pipelines
    """

    def create_pipeline(self, sections, previous):
        pipeline = []
        for section_id in sections:
            if not section_id or section_id == self.name:
                continue

            try:
                section = self.transmogrifier[section_id]
            except KeyError:
                if section_id.startswith('blueprint='):
                    section = {'blueprint': section_id[len('blueprint='):]}
                    section.update(dict([
                        (key, value) for key, value in self.options.items()
                        if key not in ['blueprint', 'pipeline']
                    ]))
                else:
                    raise

            blueprint_id = section['blueprint']
            blueprint = getUtility(ISectionBlueprint, blueprint_id)

            if not pipeline:
                pipeline = blueprint(
                    self.transmogrifier, section_id, section, previous)
            else:
                pipeline = blueprint(
                    self.transmogrifier, section_id, section, pipeline)

            if not ISection.providedBy(pipeline):
                raise ValueError('Blueprint %s for section %s did not return '
                                 'an ISection' % (blueprint_id, section_id))

        return iter(pipeline)

    def __iter__(self):
        assert not self.options.get('condition'), \
            'Support for conditional pipelines has been removed'

        # NOTE: Conditional blueprints added unnecessary complexity and
        # introduced memory issues (all non-matching items had to cached in
        # memory up to the next matching item), and broke the transmogrifier's
        # promise of serial processing.

        sections = get_lines(self.options.get('pipeline'))
        if sections:
            previous = self.create_pipeline(sections, self.previous)
        else:
            previous = self.previous
        for item in previous:
            yield item
