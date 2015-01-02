Expression sections
===================

Expression blueprints are core tools in Transmogrifier.

``transmogrifier.from`` generates items from defined expressions.

    >>> a = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': i} for i in range(3)]
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfiguration('transmogrifier.tests.expression.a', a)
    >>> Transmogrifier('transmogrifier.tests.expression.a')
    >>> print(logger)
    logger INFO
      {'id': 0}
    logger INFO
      {'id': 1}
    logger INFO
      {'id': 2}
    >>> logger.clear()

If expression does not return a mapping, the result is wrapped into a mapping.

    >>> b = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... id = range(3)
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfiguration('transmogrifier.tests.expression.b', b)
    >>> Transmogrifier('transmogrifier.tests.expression.b')
    >>> print(logger)
    logger INFO
      {'id': 0}
    logger INFO
      {'id': 1}
    logger INFO
      {'id': 2}
    >>> logger.clear()

``transmogrifier.set`` sets new keys from expression results.

    >>> c = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     setter
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': i} for i in range(3)]
    ...
    ... [setter]
    ... blueprint = transmogrifier.set
    ... title = string:item-${item['id']}
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfiguration('transmogrifier.tests.expression.c', c)
    >>> Transmogrifier('transmogrifier.tests.expression.c')
    >>> print(logger)
    logger INFO
      {'id': 0, 'title': 'item-0'}
    logger INFO
      {'id': 1, 'title': 'item-1'}
    logger INFO
      {'id': 2, 'title': 'item-2'}
    >>> logger.clear()

``transmogrifier.transform`` just executes expression, which may mutate the item or perform construction with it, but does not set new key from the results.

    >>> d = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     setter
    ...     transform
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': i} for i in range(3)]
    ...
    ... [setter]
    ... blueprint = transmogrifier.set
    ... title = string:item-${item['id']}
    ...
    ... [transform]
    ... blueprint = transmogrifier.transform
    ... expression = item.pop('title')
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfiguration('transmogrifier.tests.expression.d', d)
    >>> Transmogrifier('transmogrifier.tests.expression.d')
    >>> print(logger)
    logger INFO
      {'id': 0}
    logger INFO
      {'id': 1}
    logger INFO
      {'id': 2}
    >>> logger.clear()
