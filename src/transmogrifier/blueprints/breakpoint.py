# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import pdb

from transmogrifier.blueprints import ConditionalBlueprint
from transmogrifier.utils import is_mapping


class Breakpoint(ConditionalBlueprint):
    pdb = pdb.Pdb()

    def __iter__(self):
        for item in self.previous:
            extras = is_mapping(item) and item or {}
            if self.condition(item, **extras):
                # noinspection PyProtectedMember
                self.pdb.set_trace(sys._getframe())  # Break!
            yield item
