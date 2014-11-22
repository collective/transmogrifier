# -*- coding: utf-8 -*-
"""
This module registers *.cfg files in this as named pipelines for
transmogrifier.

"""

from configparser import RawConfigParser
from venusianconfiguration import configure
from io import StringIO
import os
import pkg_resources


# Register pipelines
for resource in pkg_resources.resource_listdir(__package__, ''):
    name, ext = os.path.splitext(resource)

    if ext == '.cfg':
        # Parse to read title and description
        data = pkg_resources.resource_string(__package__, resource)
        config = RawConfigParser()
        config.readfp(StringIO(data.decode('utf-8')))

        # Register
        configure.transmogrifier.pipeline(
            name=name,
            title=config.get('transmogrifier', 'title'),
            description=config.get('transmogrifier', 'description'),
            configuration=resource
        )
