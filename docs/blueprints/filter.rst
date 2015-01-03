Filter sections
===============

    >>> a = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     filter
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... id = range(10)
    ...
    ... [filter]
    ... blueprint = transmogrifier.filter
    ... is_greater_than = item['id'] > 4
    ... is_lower_than = item['id'] < 6
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfiguration('transmogrifier.tests.filter.a', a)
    >>> Transmogrifier('transmogrifier.tests.filter.a')
    >>> print(logger)
    logger INFO
      {'id': 5}
    >>> logger.clear()

    >>> b = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     filter
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... id = range(10)
    ...
    ... [filter]
    ... blueprint = transmogrifier.filter.and
    ... is_greater_than = item['id'] > 4
    ... is_lower_than = item['id'] < 6
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfiguration('transmogrifier.tests.filter.b', b)
    >>> Transmogrifier('transmogrifier.tests.filter.b')
    >>> print(logger)
    logger INFO
      {'id': 5}
    >>> logger.clear()

    >>> c = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     filter
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... id = range(10)
    ...
    ... [filter]
    ... blueprint = transmogrifier.filter.or
    ... is_greater_than = item['id'] > 4
    ... is_even = item['id'] % 2 == 0
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    >>> registerConfiguration('transmogrifier.tests.filter.c', c)
    >>> Transmogrifier('transmogrifier.tests.filter.c')
    >>> print(logger)
    logger INFO
      {'id': 0}
    logger INFO
      {'id': 2}
    logger INFO
      {'id': 4}
    logger INFO
      {'id': 5}
    logger INFO
      {'id': 6}
    logger INFO
      {'id': 7}
    logger INFO
      {'id': 8}
    logger INFO
      {'id': 9}
    >>> logger.clear()
