# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import importlib

from transmogrifier.blueprints import ConditionalBlueprint
from transmogrifier.expression import Expression
from transmogrifier.utils import is_mapping


def get_expressions(blueprint, blacklist=None):
    expressions = {}
    for name, value in blueprint.options.items():
        if blacklist and name in blacklist:
            continue
        expressions[name] = Expression(
            value or 'python:True',
            blueprint.transmogrifier, blueprint.name, blueprint.options
        )
    return sorted(expressions.items(), key=lambda x: x[0])


class ExpressionSource(ConditionalBlueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expressions = get_expressions(
            self, ['blueprint', 'modules', 'condition'])

        assert expressions, 'No expressions defined'

        for name, expression in expressions:
            for item in (expression(None) or []):
                if name == 'expression' and is_mapping(item):
                    if self.condition(item):
                        yield item
                else:
                    if self.condition({name: item}):
                        yield {name: item}
            break


class ExpressionTransform(ConditionalBlueprint):

    def __iter__(self):
        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expressions = get_expressions(
            self, ['blueprint', 'modules', 'condition'])

        assert expressions, 'No expressions defined'

        for item in self.previous:
            if self.condition(item) and is_mapping(item):
                for name, expression in expressions:
                    item[name] = expression(item)
            yield item


class ExpressionConstructor(ConditionalBlueprint):
    def __iter__(self):
        mode = self.options.get('mode', 'item')
        assert mode in ('each', 'all', 'item', 'items')

        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expressions = get_expressions(
            self, ['blueprint', 'modules', 'condition'])

        assert expressions, 'No expressions defined'

        items = []
        for item in self.previous:
            if self.condition(item):
                items.append(item)
                if mode in ('each', 'item'):
                    for name, expression in expressions:
                        expression(item, items=items)
                        break
            yield item

        if mode in ('all', 'items'):
            for name, expression in expressions:
                expression(None, items=items)
                break


class ExpressionFilter(ConditionalBlueprint):
    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                yield item
