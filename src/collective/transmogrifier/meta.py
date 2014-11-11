from zope.component.zcml import IUtilityDirective
from zope.component.zcml import utility
from zope.configuration.fields import MessageID
from zope.configuration.fields import Path
from zope.configuration.fields import PythonIdentifier
from zope.interface import Interface
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from transmogrifier import configuration_registry

#### transmogrifier:registerConfig

class IPipelineDirective(Interface):

    """Register pipeline configurations with the global registry.
    """

    name = PythonIdentifier(
        title=u'Name',
        description=u"If not specified 'default' is used.",
        default=u'default',
        required=False)

    title = MessageID(
        title=u'Title',
        description=u'Optional title for the pipeline configuration.',
        default=None,
        required=False)

    description = MessageID(
        title=u'Description',
        description=u'Optional description for the pipeline configuration.',
        default=None,
        required=False)

    configuration = Path(
        title=u'Configuration',
        description=u"The pipeline configuration file to register.",
        required=True)

IRegisterConfigDirective = IPipelineDirective  # BBB

class IBlueprintDirective(IUtilityDirective):

    """Section blueprint
    """

_configuration_regs = []
def pipeline(_context, configuration, name=u'default', title=None,
                   description=None):
    """Register new pipeline into the global registry
    """
    if title is None:
        title = u"Pipeline configuration '%s'" % name

    if description is None:
        description = u''

    _configuration_regs.append('%s' % name)

    _context.action(
        discriminator=('registerConfig', name),
        callable=configuration_registry.registerConfiguration,
        args=(name, title, description, configuration))

registerConfig = pipeline

def blueprint(_context, provides=ISectionBlueprint, component=None,
              factory=None, permission=None, name=u''):
    assert ISection in component.__implemented__
    utility(_context, provides=provides, component=component,
            factory=factory, permission=permission, name=name)
