####
FX Bitstamp
####

This project is about a trading system for Bitcoins intended to be applied to the `Bitstamp.net <http://bitstamp.net>`_ exchange. But it can also be used with other exchanges provided these offer a JSON based API.

The basic idea of the system is to model the trading quotes as a stream/pipe of data, and offer small tools that take the stream, apply a specific operation to it and hand it over to the next tool in the processing chain.

This approach has been loosely inspired by the UNIX approach, where the whole system is simply a collection of simple commands that do their job well. A crucial difference is though the fact the UNIX commands work in general on a hierarchical file system as a source and/or target of data, whereas here the quote stream is used as a carrier of data instead.

Quote Stream
************

The actual data in the stream is JSON-like, and some example quotations might look like the following:

.. code:: json
  
  {"volume": "10482.13511879", "last": "117.80", "timestamp": 1368230343.756902, "bid": "117.15", "high": "119.98", "low": "109.20", "ask": "117.90"}
  {"volume": "10482.48787536", "last": "117.90", "timestamp": 1368230351.260416, "bid": "117.90", "high": "119.98", "low": "109.20", "ask": "117.95"}
  {"volume": "10479.48787536", "last": "117.90", "timestamp": 1368230353.784478, "bid": "117.90", "high": "119.98", "low": "109.20", "ask": "117.95"}
  ...

According to the official JSON specification the double quote delimiters ``"`` are mandatory, but each tool in the processing chain also accepts entries where single quote delimiters ``'`` are used. More importantly each of them *produces* tuples with single quote delimiters (due to some implementation details).

The structure of the tuple is arbitrary, except for `timestamp` which is always required. The `volume`, `high` and `low` values are for the last 24 hours; `last`, `bid` and `ask` contain the most recent values.

`last`
  USD value paid for a Bitcoin in the most recent transactions;
`bid`
  highest bid price in USD somebody is currently willing pay for a BTC;
`ask`
  lowest ask prices in USD for which somebody is willing to sell a BTC at;
`high`
  highest transaction price in USD in the last 24 hours;
`low`
  lowest transaction price in USD in the last 24 hours;
`volume`
  number of BTCs traded in the last 24 hours;
`timestamp`
  UNIX timestamp for current quote;


