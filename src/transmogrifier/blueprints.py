# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import StringIO
from csv import DictReader
from csv import DictWriter
import os
import sys

from zope.interface import provider
from zope.interface import implementer

from transmogrifier.condition import Condition
from transmogrifier.expression import Expression

from transmogrifier.interfaces import ISectionBlueprint
from transmogrifier.interfaces import ISection

import logging
logger = logging.getLogger('transmogrifier')


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


@provider(ISectionBlueprint)
@implementer(ISection)
class EmptyDictionarySection(ConditionalBlueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        try:
            amount = int(self.options.get('amount') or '1')
        except (TypeError, ValueError):
            amount = 1

        for i in range(amount):
            yield {}


@provider(ISectionBlueprint)
@implementer(ISection)
class FromCSVSection(ConditionalBlueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        path = self.options.get('filename', 'input.csv').strip()

        if path != '-' and not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        fb_buffer = StringIO()
        if path == '-':
            fb_buffer.write(sys.stdin.read())
        else:
            with open(path, 'r') as fb_input:
                fb_buffer.write(fb_input.read())
        fb_buffer.seek(0)

        reader = DictReader(fb_buffer)
        for row in reader:
            yield row


@provider(ISectionBlueprint)
@implementer(ISection)
class FromExpressionSection(Blueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        expression = Expression(
            self.options.get('expression') or 'python:[{}]',
            self.transmogrifier, self.name, self.options
        )
        for item in expression(None):
            yield item


@provider(ISectionBlueprint)
@implementer(ISection)
class ExpressionSection(ConditionalBlueprint):
    def __iter__(self):
        expressions = {}
        for name, value in self.options.items():
            if name in ['blueprint', 'condition'] or not name.startswith('_'):
                continue
            expressions[name] = Expression(
                value or 'python:True',
                self.transmogrifier, self.name, self.options
            )
        for item in self.previous:
            if self.condition(item):
                item.update(dict([
                    (name, expression(item))
                    for name, expression in expressions.items()
                ]))
            yield item


@provider(ISectionBlueprint)
@implementer(ISection)
class ToCSVSection(ConditionalBlueprint):
    def __iter__(self):
        path = self.options.get('filename', 'output.csv').strip()
        fieldnames = filter(bool, self.options.get('fieldnames', '').split())

        if path != '-' and not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        fp = StringIO()
        writer = DictWriter(fp, list(fieldnames))

        counter = 0
        for item in self.previous:
            if self.condition(item) and isinstance(item, dict):
                if not writer.fieldnames:
                    writer.fieldnames = item.keys()
                if counter == 0:
                    writer.writeheader()

                clone = item.copy()
                for fieldname in writer.fieldnames:
                    clone.setdefault(fieldname, None)
                writer.writerow(dict([
                    (key, value) for key, value in clone.items()
                    if key in writer.fieldnames
                ]))
                counter += 1

            yield item
        fp.seek(0)

        if path == '-':
            sys.stdout.write(fp.read())
        else:
            with open(path, 'w') as fp2:
                fp2.write(fp.read())

        logger.info('{0:s}:{1:s} saved {2:d} items to {3:s}'.format(
            self.__class__.__name__, self.name, counter, path,
            self.options.get('filename', 'output.csv')
        ))
