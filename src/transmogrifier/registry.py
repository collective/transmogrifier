# -*- coding: utf-8 -*-
import pkg_resources


# noinspection PyPep8Naming
class ConfigurationRegistry(object):
    def __init__(self):
        self._config_info = {}
        self._config_ids = []

    def clear(self):
        self._config_info = {}
        self._config_ids = []

    def registerConfiguration(self, name, title, description, configuration):
        if name in self._config_info:
            raise KeyError('Duplicate pipeline configuration: %s' % name)

        self._config_ids.append(name)
        self._config_info[name] = dict(
            id=name,
            title=title,
            description=description,
            configuration=configuration
        )

    def getConfiguration(self, id_):
        return self._config_info[id_].copy()

    def listConfigurationIds(self):
        return tuple(self._config_ids)


configuration_registry = ConfigurationRegistry()


try:
    from zope.testing.cleanup import addCleanUp
except ImportError:
    addCleanUp = lambda x: None  # noqa
else:
    addCleanUp(configuration_registry.clear)
    del addCleanUp


# BBB: Support collective.transmogrifier
try:
    pkg_resources.get_distribution('collective.transmogrifier')
    from collective.transmogrifier.transmogrifier import configuration_registry  # noqa
except pkg_resources.DistributionNotFound:
    pass
