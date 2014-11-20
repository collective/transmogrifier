# -*- coding: utf-8 -*-
"""
This module scans all direct submodules for component registrations in this
package when included for zope.configuration with venusianconfiguration.

"""
import importlib
import os

from venusianconfiguration import configure
from venusianconfiguration import scan
import pkg_resources


# Scan modules
for resource in pkg_resources.resource_listdir(__package__, ''):
    name, ext = os.path.splitext(resource)
    if ext == '.py' and name not in ('__init__', 'configure'):
        path = '{0:s}.{1:s}'.format(__package__, name)
        scan(importlib.import_module(path))


# Include pipelines
import pipelines
configure.include(package=pipelines, file='configure.py')
