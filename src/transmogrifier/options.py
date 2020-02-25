# -*- coding: utf-8 -*-
from future.moves.collections import UserDict
import re


class Options(UserDict):
    def __init__(self, transmogrifier, section, data):
        self.transmogrifier = transmogrifier
        self.section = section
        self._data = data
        self._cooked = {}
        self.data = {}

    def substitute(self):
        for key, value in self._data.items():
            if '${' in value:
                self._cooked[key] = self._sub(value, [(self.section, key)])

    def get(self, option, default=None, seen=None):
        try:
            return self.data[option]
        except KeyError:
            pass

        value = self._cooked.get(option)
        if value is None:
            value = self._data.get(option)
            if value is None:
                return default

        if '${' in value:
            key = self.section, option
            if seen is None:
                seen = [key]
            elif key in seen:
                raise ValueError('Circular reference in substitutions.')
            else:
                seen.append(key)

            value = self._sub(value, seen)
            seen.pop()

        self.data[option] = value
        return value

    _template_split = re.compile(r'([$]{[^}]*})').split
    _valid = re.compile(r'\${[-a-zA-Z0-9 ._]*:[-a-zA-Z0-9 ._]+}$').match
    _tales = re.compile(r'^\s*string:', re.MULTILINE).match

    def _sub(self, template, seen):
        parts = self._template_split(template)
        subs = []
        for ref in parts[1::2]:
            if not self._valid(ref):
                # A value with a string: TALES expression?
                if self._tales(template):
                    subs.append(ref)
                    continue
                raise ValueError('Not a valid substitution %s.' % ref)

            names = tuple(ref[2:-1].split(':'))
            if not names[0]:
                names = seen[0][0], names[1]
            value = self.transmogrifier[names[0]].get(names[1], None, seen)
            if value is None:
                raise KeyError('Referenced option does not exist:', *names)
            subs.append(value)
        subs.append('')

        return ''.join([''.join(v) for v in zip(parts[::2], subs)])

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            pass

        v = self.get(key)
        if v is None:
            raise KeyError('Missing option: %s:%s' % (self.section, key))
        return v

    def __setitem__(self, option, value):
        if not isinstance(value, str):
            raise TypeError('Option values must be strings', value)
        self.data[option] = value

    def __delitem__(self, key):
        if key in self._data:
            del self._data[key]
            if key in self.data:
                del self.data[key]
            if key in self._cooked:
                del self._cooked[key]
        elif key in self.data:
            del self.data[key]
        else:
            raise KeyError(key)

    def copy(self):
        result = self._data.copy()
        result.update(self._cooked)
        result.update(self.data)
        return result

    def keys(self):
        for key in self._data:
            yield key
        for key in [k for k in self.data if k not in self._data]:
            yield key

    def has_key(self, key):
        return key in self.keys()

    def iterkeys(self):
        for key in self.keys():
            yield key

    def items(self):
        for key in self.keys():
            yield key, self[key]

    iteritems = items

    def values(self):
        for key in self.keys():
            yield self[key]

    itervalues = values

    def __len__(self):
        return len(list(self.keys()))

    def __iter__(self):
        for k in self.keys():
            yield k

    def __contains__(self, key):
        return key in self.keys()
