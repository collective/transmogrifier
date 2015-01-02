# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import importlib

from transmogrifier.blueprints import Blueprint
from transmogrifier.blueprints import ConditionalBlueprint
from transmogrifier.expression import Expression
from transmogrifier.utils import is_mapping

from zope.interface.exceptions import BrokenImplementation

import pkg_resources

try:
    pkg_resources.get_distribution('Acquisition')
except pkg_resources.DistributionNotFound:
    HAS_ACQUISITION = False
else:
    import Acquisition
    HAS_ACQUISITION = True


def unwrap(item):
    """Unwrap objects from known wrappings"""
    if HAS_ACQUISITION:
        # noinspection PyUnresolvedReferences
        return Acquisition.aq_base(item)
    else:
        return item


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
    """Generate items from expressions result"""
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
                try:
                    if is_mapping(unwrap(item)):
                        if self.condition(item):
                            yield item
                except BrokenImplementation:
                    if self.condition({name: item}):
                        yield {name: item}
            break


class ExpressionSetter(ConditionalBlueprint):
    """Set item keys from expressions result"""
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


class ExpressionTransform(ConditionalBlueprint):
    """Executes expressions with items allowing transform or construction"""
    def __iter__(self):
        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expressions = get_expressions(
            self, ['blueprint', 'modules', 'condition'])

        assert expressions, 'No expressions defined'

        for item in self.previous:
            if self.condition(item):
                for name, expression in expressions:
                    expression(item)
            yield item


class ExpressionFilterAnd(Blueprint):
    """Filter items by expressions (AND)"""
    def __iter__(self):
        expressions = get_expressions(self, ['blueprint', 'modules'])
        for item in self.previous:
            try:
                for name, expression in expressions:
                    assert bool(expression(item)), 'Condition failed'
                yield item
            except AssertionError:
                pass


class ExpressionFilterOr(Blueprint):
    """Filter items by expressions (OR)"""
    def __iter__(self):
        expressions = get_expressions(self, ['blueprint', 'modules'])
        for item in self.previous:
            for name, expression in expressions:
                if bool(expression(item)):
                    yield item
                    break


class ExpressionInterval(ConditionalBlueprint):
    """Perform standalone expressions by defined interval"""
    def __iter__(self):
        modules = filter(bool, map(
            str.strip, self.options.get('modules', '').split()))
        for module in modules:
            importlib.import_module(module)

        expressions = get_expressions(
            self, ['blueprint', 'modules', 'condition', 'interval'])

        assert expressions, 'No expressions defined'

        counter = interval = int(self.options.get('interval', '1'))

        for item in self.previous:
            if self.condition(item):
                counter -= 1
                if counter == 0:
                    for name, expression in expressions:
                        expression(None)
                    counter = interval
            yield item

        if counter != interval:
            for name, expression in expressions:
                expression(None)
