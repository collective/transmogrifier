# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import StringIO
from io import BytesIO
from csv import DictReader
from csv import DictWriter
import os
import sys
import logging

from transmogrifier.blueprints import Blueprint
from transmogrifier.blueprints import ConditionalBlueprint
from transmogrifier.utils import is_mapping


logger = logging.getLogger('transmogrifier')


class DelTransform(ConditionalBlueprint):
    def __iter__(self):
        keys = [key.strip() for key in self.options.get('keys', '').split()]
        for item in self.previous:
            if self.condition(item):
                for key in keys:
                    if key in item:
                        del item[key]
            yield item


class InvertTransform(ConditionalBlueprint):
    def __iter__(self):
        key = self.options.get('key')
        for item in self.previous:
            if self.condition(item) and is_mapping(item.get(key)):
                inverted = item.pop(key)
                for key_, value in item.items():
                    inverted[key_] = value
                yield inverted
            else:
                yield item


class CodecTransform(ConditionalBlueprint):
    def __iter__(self):
        transforms = {}
        for name, value in self.options.items():
            if name in ['blueprint', 'condition']:
                continue
            from_, to_ = [s.strip() for s in value.strip().split(':')]
            transforms[name] = (from_, to_)

        for item in self.previous:
            if self.condition(item):
                for name, value in transforms.items():
                    if name not in item:
                        continue
                    if value[0] != 'unicode':
                        if hasattr(item[name], 'decode'):
                            item[name] = item[name].decode(value[0])
                    if value[1] != 'unicode':
                        item[name] = item[name].encode(value[1])
            yield item


class CSVSource(Blueprint):
    def __iter__(self):
        for item in self.previous:
            yield item

        path = self.options.get('filename', 'input.csv').strip()

        if path != '-' and not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        fb_buffer = BytesIO()
        if path == '-':
            fb_buffer.write(sys.stdin.read())
        else:
            with open(path, 'r') as fb_input:
                fb_buffer.write(fb_input.read())
        fb_buffer.seek(0)

        reader = DictReader(fb_buffer)
        for row in reader:
            yield row


class CSVConstructor(ConditionalBlueprint):
    def __iter__(self):  # flake8: noqa
        path = self.options.get('filename', 'output.csv').strip()
        fieldnames = filter(bool, self.options.get('fieldnames', '').split())

        if path != '-' and not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        if sys.version_info[0] < 3:
            fp = BytesIO()
        else:
            fp = StringIO()
        writer = DictWriter(fp, list(fieldnames))

        counter = 0
        for item in self.previous:
            if self.condition(item) and is_mapping(item):
                if not writer.fieldnames:
                    writer.fieldnames = [key for key in item.keys()
                                         if not key.startswith('_')]
                if counter == 0:
                    header = dict(zip(writer.fieldnames, writer.fieldnames))
                    writer.writerow(header)

                clone = dict(item)
                for fieldname in writer.fieldnames:
                    clone.setdefault(fieldname, None)
                writer.writerow(dict([
                    (key, value) for key, value in clone.items()
                    if key in writer.fieldnames
                ]))
                counter += 1

            yield item
        fp.seek(0)

        if path == '-':
            sys.stdout.write(fp.read())
        else:
            with open(path, 'w') as fp2:
                fp2.write(fp.read())

        logger.info('{0:s}:{1:s} wrote {2:d} items to {3:s}'.format(
            self.__class__.__name__, self.name, counter, path,
            self.options.get('filename', 'output.csv')
        ))
