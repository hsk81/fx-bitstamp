#!/usr/bin/env python

###############################################################################
###############################################################################

__author__ = 'hsk81'

###############################################################################
###############################################################################

import do
import numpy

###############################################################################
###############################################################################

class DiffLogCallable (object):

    def __call__ (self, *args: list) -> numpy.array:
        return numpy.diff (numpy.log (args))

    def __repr__ (self) -> str:
        return 'diff (log (@{0}))'

###############################################################################
###############################################################################

if __name__ == "__main__":
    args = do.get_arguments ({
        'function': DiffLogCallable (), 'result': 'diff-log'
    })

    try: do.loop (args.function, args.parameters, args.result,
        verbose=args.verbose)

    except KeyboardInterrupt:
        pass

###############################################################################
###############################################################################
