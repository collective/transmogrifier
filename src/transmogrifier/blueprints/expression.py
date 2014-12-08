# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import importlib

from transmogrifier.blueprints import Blueprint
from transmogrifier.blueprints import ConditionalBlueprint

from transmogrifier.expression import Expression

import logging
logger = logging.getLogger('transmogrifier')


class ExpressionSource(Blueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expression = Expression(
            self.options.get('expression') or 'python:[{}]',
            self.transmogrifier, self.name, self.options
        )

        key = self.options.get('key')
        for item in (expression(None) or []):
            if key:
                yield {key: item}
            else:
                yield item


class ExpressionTransform(ConditionalBlueprint):
    def __iter__(self):
        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expressions = {}
        for name, value in self.options.items():
            if name in ['blueprint', 'modules', 'condition']:
                continue
            expressions[name] = Expression(
                value or 'python:True',
                self.transmogrifier, self.name, self.options
            )
        expressions = sorted(expressions.items(), key=lambda x: x[0])

        for item in self.previous:
            if isinstance(item, dict):
                item_transformed = item
            else:
                item_transformed = {}
            if self.condition(item):
                for name, expression in expressions:
                    item_transformed[name] = expression(item)
            yield item_transformed


class ExpressionConstructor(ConditionalBlueprint):
    def __iter__(self):
        mode = self.options.get('mode', 'item')
        assert mode in ('each', 'all', 'item', 'items')

        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expression = Expression(
            self.options.get('expression') or 'python:True',
            self.transmogrifier, self.name, self.options
        )

        items = []
        for item in self.previous:
            if self.condition(item):
                items.append(item)
                if mode in ('each', 'item'):
                    expression(item, items=items)
            yield item

        if mode in ('all', 'items'):
            expression(None, items=items)


class ExpressionFilter(ConditionalBlueprint):
    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                yield item


# transmogrify/regexp
# by aclark

class RegExpTransform(ConditionalBlueprint):
    def __iter__(self):
        try:
            key = self.options['key']
            regexp = re.compile(self.options['expression'])
            strfmt = self.options['format'].replace('%%', '%')
            order = [int(s.strip()) for s in self.options['order'].split(',')]
        except KeyError as e:
            raise SyntaxError('Must specify \'{0:s}\''.format(e))

        for item in self.previous:
            if self.condition(item):
                result = regexp.search(item[key])
                if result and result.groups():
                    item[key] = \
                        strfmt % tuple([result.groups()[i] for i in order])
            yield item
