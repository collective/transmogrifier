# -*- coding: utf-8 -*-
from logging import getLogger
from logging import DEBUG
import sys

try:
    from zope.pagetemplate import engine
    HAS_EXPRESSION = True
    HAS_CONDITION = True
except ImportError:
    # BBB: Zope 2.10
    try:
        from zope.app.pagetemplate import engine
        HAS_EXPRESSION = True
        HAS_CONDITION = True
    except ImportError:
        HAS_EXPRESSION = False
        HAS_CONDITION = False

from collective.transmogrifier.utils import pformat_msg


class Expression(object):
    """A transmogrifier expression

    Evaluate the expression with a transmogrifier context.

    """
    def __init__(self, expression, transmogrifier, name, options, **extras):
        self.expression = engine.TrustedEngine.compile(expression)
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.extras = extras
        logger_base = getattr(transmogrifier, 'configuration_id',
                              'transmogrifier')
        self.logger = getLogger(logger_base + '.' + name)

    def __call__(self, item, **extras):
        extras.update(self.extras)
        result = self.expression(engine.TrustedEngine.getContext(
            item=item,
            transmogrifier=self.transmogrifier,
            name=self.name,
            options=self.options,
            nothing=None,
            modules=sys.modules,
            **extras
        ))
        if self.logger.isEnabledFor(DEBUG):
            formatted = pformat_msg(result)
            self.logger.debug('Expression returned: %s', formatted)
        return result


class Condition(Expression):
    """A transmogrifier condition expression

    Test if a pipeline item matches the given TALES expression.

    """
    def __call__(self, item, **extras):
        return bool(super(Condition, self).__call__(item, **extras))