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

class InverseCallable (object):

    def __call__ (self, *args: list) -> numpy.array:
        return 1.0 / numpy.array (args)

    def __repr__ (self) -> str:
        return '1.0 / @{0}'

###############################################################################
###############################################################################

if __name__ == "__main__":
    args = do.get_arguments ({
        'function': InverseCallable (), 'result': 'inverse'
    })

    try: do.loop (args.function, args.parameters, args.result,
        verbose=args.verbose)

    except KeyboardInterrupt:
        pass

###############################################################################
###############################################################################
