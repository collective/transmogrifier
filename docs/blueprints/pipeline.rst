Pipeline section
================

    >>> a = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     pipeline
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': 'item-{0:02d}'.format(i)}
    ...               for i in range(3)]
    ...
    ... [pipeline]
    ... blueprint = transmogrifier.pipeline
    ... pipeline =
    ...     logger
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... key = id
    ... """
    >>> registerConfiguration('transmogrifier.tests.pipeline.a', a)
    >>> Transmogrifier('transmogrifier.tests.pipeline.a')
    >>> print(logger)
    logger INFO
      item-00
    logger INFO
      item-01
    logger INFO
      item-02
    >>> logger.clear()

    >>> b = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     transform-pipeline
    ...     logger-pipeline
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': 'item-{0:02d}'.format(i)}
    ...               for i in range(3)]
    ...
    ... [transform-pipeline]
    ... blueprint = transmogrifier.pipeline
    ... condition = item['id'] == 'item-01'
    ... pipeline =
    ...     transform-upper
    ...     transform-concat
    ...
    ... [transform-upper]
    ... blueprint = transmogrifier.set
    ... id = item['id'].upper()
    ...
    ... [transform-concat]
    ... blueprint = transmogrifier.set
    ... id = ' '.join([item['id'], item['id']])
    ...
    ... [logger-pipeline]
    ... blueprint = transmogrifier.pipeline
    ... pipeline =
    ...     logger
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... key = id
    ... """
    >>> registerConfiguration('transmogrifier.tests.pipeline.b', b)
    >>> Transmogrifier('transmogrifier.tests.pipeline.b')
    >>> print(logger)
    logger INFO
      item-00
    logger INFO
      ITEM-01 ITEM-01
    logger INFO
      item-02
    >>> logger.clear()

    >>> c = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     placeholder
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': 'item-{0:02d}'.format(i)}
    ...               for i in range(3)]
    ...
    ... [placeholder]
    ... blueprint = transmogrifier.pipeline
    ... pipeline =
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... key = id
    ... """
    >>> registerConfiguration('transmogrifier.tests.pipeline.c', c)
    >>> Transmogrifier('transmogrifier.tests.pipeline.c')
    >>> print(logger)
    logger INFO
      item-00
    logger INFO
      item-01
    logger INFO
      item-02
    >>> logger.clear()
