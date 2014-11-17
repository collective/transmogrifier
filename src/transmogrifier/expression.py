# -*- coding: utf-8 -*-
import functools
from logging import getLogger
from logging import DEBUG
import sys

from six import text_type as u

from chameleon import tales
from chameleon.astutil import Builtin

from chameleon.compiler import ExpressionEngine
from chameleon.compiler import ExpressionEvaluator
from chameleon.tales import ExpressionParser
from chameleon.tales import match_prefix

from transmogrifier.utils import pformat_msg


try:
    from z3c.pt import expressions
    HAS_Z3C_PT = True
except ImportError:
    expressions = None
    HAS_Z3C_PT = False

DEFAULT_EXPRESSION_TYPE = 'python'


class Expression(object):
    """A transmogrifier expression

    Evaluate the expression with a transmogrifier context.

    """
    def __init__(self, expression, transmogrifier, name, options, **extras):
        self.expression = expression
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.extras = extras

        if HAS_Z3C_PT:
            self.expression_types = {
                'python': expressions.PythonExpr,
                'string': tales.StringExpr,
                'not': tales.NotExpr,
                'exists': expressions.ExistsExpr,
                'path': expressions.PathExpr,
                'provider': expressions.ProviderExpr,
                'nocall': expressions.NocallExpr,
            }
        else:
            self.expression_types = {
                'python': tales.PythonExpr,
                'string': tales.StringExpr,
                'not': tales.NotExpr,
                'exists': tales.ExistsExpr,
                'import': tales.ImportExpr,
                'structure': tales.StructureExpr,
            }

        parser = ExpressionParser(self.expression_types,
                                  DEFAULT_EXPRESSION_TYPE)
        engine = functools.partial(ExpressionEngine, parser,
                                   default_marker=Builtin('False'))
        self.evaluator = ExpressionEvaluator(engine, {
            'nothing': None,
            'modules': sys.modules
        })

        logger_base = getattr(
            transmogrifier, 'configuration_id', 'transmogrifier')
        self.logger = getLogger(logger_base + '.' + name)

    def __call__(self, item, **extras):
        context = {
            'item': item,
            'transmogrifier': self.transmogrifier,
            'name': self.name,
            'options': self.options,
            'nothing': None,
            'modules': sys.modules,
        }
        context.update(self.extras)
        context.update(extras)

        m = match_prefix(self.expression)
        if m is not None:
            prefix = m.group(1)
            expr = self.expression[m.end():]
        else:
            prefix = DEFAULT_EXPRESSION_TYPE
            expr = self.expression

        result = self.evaluator(context, {}, prefix, expr)

        if self.logger.isEnabledFor(DEBUG):
            formatted = pformat_msg(result)
            self.logger.debug(
                u('Expression returned: {0:s}'.format(formatted)))
        return result