Logger section
==============

A logger section lets you log a piece of data from the item together with a name. You can set any logging level in the logger. The logger blueprint name is ``transmogrifier.sections.logger``.

    >>> a = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': 'item-{0:02d}'.format(i)}
    ...               for i in range(3)]
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... key = id
    ... """
    >>> registerConfiguration('transmogrifier.tests.logger.a', a)
    >>> Transmogrifier('transmogrifier.tests.logger.a')
    >>> print(logger)
    logger INFO
      item-00
    logger INFO
      item-01
    logger INFO
      item-02
    >>> logger.clear()

We can also have numerical levels, and if the key is missing, it will print out a message to that effect. A condition may also be used to restrict the items logged.

    >>> b = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': 'item-{0:02d}'.format(i)}
    ...               for i in range(3)]
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... condition = python:item['id'] != 'item-01'
    ... level = 10
    ... name = logger
    ... key = foo
    ... """
    >>> registerConfiguration('transmogrifier.tests.logger.b', b)
    >>> Transmogrifier('transmogrifier.tests.logger.b')
    >>> print(logger)
    logger DEBUG
       -- Missing key --
    logger DEBUG
       -- Missing key --
    >>> logger.clear()

If no ``key`` option is given, the logger will render the whole item in a readable format using Python's ``pprint`` module.  The ``delete`` option can be used to omit certain keys from the output, such as body text fields which may be too large and make the output too noisy.

    >>> c = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     duplicate
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': 'item-{0:02d}'.format(i)}
    ...               for i in range(3)]
    ...
    ... [duplicate]
    ... blueprint = transmogrifier.set
    ... id-duplicate = python:item['id']
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... delete =
    ...     id-duplicate
    ...     nonexistent
    ... """
    >>> registerConfiguration('transmogrifier.tests.logger', c)
    >>> Transmogrifier('transmogrifier.tests.logger')
    >>> print(logger)
    logger INFO
      {'id': 'item-00'}
    logger INFO
      {'id': 'item-01'}
    logger INFO
      {'id': 'item-02'}
    >>> logger.clear()
