#!/usr/bin/env python

###############################################################################
###############################################################################

__author__ = 'hsk81'

###############################################################################
###############################################################################

from map import get_arguments, loop
import numpy

###############################################################################
###############################################################################

if __name__ == "__main__":

    args = get_arguments ({'function': [
        [lambda *values: numpy.log (numpy.array (list (map (float, values))))]
    ]})

    try: loop (args.function, args.parameter_group, args.result,
        verbose=args.verbose)

    except KeyboardInterrupt:
        pass

###############################################################################
###############################################################################
