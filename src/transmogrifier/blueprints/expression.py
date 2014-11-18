# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from transmogrifier.blueprints import Blueprint
from transmogrifier.blueprints import ConditionalBlueprint

from transmogrifier.expression import Expression

import logging
logger = logging.getLogger('transmogrifier')


class ExpressionSource(Blueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        expression = Expression(
            self.options.get('expression') or 'python:[{}]',
            self.transmogrifier, self.name, self.options
        )
        for item in expression(None):
            yield item


class ExpressionTransform(ConditionalBlueprint):
    def __iter__(self):
        expressions = {}
        for name, value in self.options.items():
            if name in ['blueprint', 'condition'] or name.startswith('_'):
                continue
            expressions[name] = Expression(
                value or 'python:True',
                self.transmogrifier, self.name, self.options
            )
        for item in self.previous:
            if isinstance(item, dict):
                item_transformed = item
            else:
                item_transformed = {}
            if self.condition(item):
                item_transformed.update(dict([
                    (name, expression(item))
                    for name, expression in expressions.items()
                ]))
            yield item_transformed


class ExpressionFilter(ConditionalBlueprint):
    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                yield item
