# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import pdb

from transmogrifier.blueprints import ConditionalBlueprint

import logging
logger = logging.getLogger('transmogrifier')


class Breakpoint(ConditionalBlueprint):
    pdb = pdb.Pdb()

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                self.pdb.set_trace(sys._getframe())  # Break!
                self.pdb.set_trace(sys._getframe().f_back)  # Break!
            yield item
