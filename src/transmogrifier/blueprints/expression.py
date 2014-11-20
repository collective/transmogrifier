# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
        for item in (expression(None) or []):
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


class ExpressionFilter(ConditionalBlueprint):
    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                yield item