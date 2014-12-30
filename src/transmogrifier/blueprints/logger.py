# -*- coding: utf-8 -*-
import logging

from transmogrifier.blueprints import ConditionalBlueprint
from transmogrifier.utils import Matcher
from transmogrifier.utils import pformat_msg


# from collective/transmogrifier/sections/logger.py
# by rpatterson, regebro

class Logger(ConditionalBlueprint):
    def __iter__(self):
        # Get options
        key = self.options.get('key')
        delete = Matcher(*self.options.get('delete', '').splitlines())

        # Define logger
        name = self.options.get(
            'name', self.transmogrifier.configuration_id + '.' + self.name)
        logger = logging.getLogger(name)

        # Set log level
        level = self.options.get('level', logging.getLevelName(logger.level))
        level = getattr(logging, level, None) or int(level)
        logger.setLevel(level)

        for item in self.previous:
            if logger.isEnabledFor(level) and self.condition(item):
                if key is None:
                    copy = {}
                    for key_ in item.keys():
                        if not delete(key_)[1]:
                            copy[key_] = item[key_]
                    msg = pformat_msg(copy)
                elif key in item:
                    msg = pformat_msg(item[key])
                else:
                    msg = '-- Missing key --'
                logger.log(level, msg)
            yield item
