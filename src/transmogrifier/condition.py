# -*- coding: utf-8 -*-
from transmogrifier.expression import Expression


class Condition(Expression):
    """A transmogrifier condition expression

    Test if a pipeline item matches the given TALES expression.

    """
    def __call__(self, item, **extras):
        return bool(super(Condition, self).__call__(item, **extras))
