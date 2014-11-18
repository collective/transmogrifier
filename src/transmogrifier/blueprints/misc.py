# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from transmogrifier.blueprints import Blueprint

import logging
logger = logging.getLogger('transmogrifier')


class ItemSource(Blueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        try:
            amount = int(self.options.get('amount') or '1')
        except (TypeError, ValueError):
            amount = 1

        for i in range(amount):
            yield {}
