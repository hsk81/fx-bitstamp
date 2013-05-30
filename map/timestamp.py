#!/usr/bin/env python

###############################################################################
###############################################################################

__author__ = 'hsk81'

###############################################################################
###############################################################################

import do
import datetime as dt

###############################################################################
###############################################################################

class FromTimestampCallable (object):

    def __call__ (self, *args: list) -> map:
        return map (str, map (dt.datetime.fromtimestamp, args))

    def __repr__ (self) -> str:
        return 'map (str, map (dt.datetime.fromtimestamp ({0}))'

###############################################################################
###############################################################################

if __name__ == "__main__":

    args = do.get_arguments ({
        'function': [[FromTimestampCallable ()]],
        'parameter-group': [['timestamp']],
        'result': [['timestamp']]
    })

    try: do.loop (args.function, args.parameter_group, args.result,
        verbose=args.verbose)

    except KeyboardInterrupt:
        pass

###############################################################################
###############################################################################
