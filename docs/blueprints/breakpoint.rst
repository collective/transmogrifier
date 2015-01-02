Breakpoint section
==================

A breakpoint section will stop and enter pdb when a specific condition is met. This is useful for debugging, as you can add a brekpoint section just before a section that gets an error on a specific item.

The alternative is to add a conditional breakpoint in the section that fails, but that can require finding the code in some egg somewhere, adding the breakpoint and restarting the server. This speeds up the process.

    >>> breakpoint = """
    ... [transmogrifier]
    ... pipeline =
    ...     source
    ...     breakpoint
    ...     logger
    ...
    ... [source]
    ... blueprint = transmogrifier.from
    ... expression = [{'id': 'item-{0:02d}'.format(i)}
    ...               for i in range(3)]
    ...
    ... [breakpoint]
    ... blueprint = transmogrifier.breakpoint
    ... condition = python: item['id'] == 'item-01'
    ...
    ... [logger]
    ... blueprint = transmogrifier.logger
    ... name = logger
    ... level = INFO
    ... """
    ...
    >>> registerConfiguration('transmogrifier.tests.breakpoint', breakpoint)

Since pdb requires input, for this test we replace stdin with something giving some input (just a continue command).

    >>> class Continue(object):
    ...     def readline(self):
    ...         print('c')
    ...         return 'c\n'

    >>> import sys
    >>> stdin = sys.stdin
    >>> sys.stdin = Continue()
    ...

    >>> Transmogrifier('transmogrifier.tests.breakpoint')
    (Pdb) c

    >>> print(logger)
    logger INFO
        {'id': 'item-00'}
    logger INFO
        {'id': 'item-01'}
    logger INFO
        {'id': 'item-02'}
    >>> logger.clear()

And finally we reset the stdin:

    >>> sys.stdin = stdin

