# An FX trader for Bitstamp.net

This project is about a trading system for Bitcoins intended to be applied to the [Bitstamp.net](http://bitstamp.net) exchange. But it can also be used with other exchanges provided these offer a JSON based API.

The basic idea of the system is to model the trading quotes as a stream/pipe of data, and offer small tools that take the stream, apply a specific operation to it and hand it over to the next tool in the processing chain.

This approach has been loosely inspired by the UNIX approach, where the whole system is simply a collection of simple commands that do their job well. A crucial difference is though the fact the UNIX commands work in general on a hierarchical file system as a source and/or target of data, whereas here the quote stream is used as a carrier of data instead.

## Quote Stream

The actual data in the stream is JSON-like, and some example quotations might look like the following:
``` json
{"volume": "10482.13511879", "last": "117.80", "timestamp": 1368230343.756902, "bid": "117.15", "high": "119.98", "low": "109.20", "ask": "117.90"}
{"volume": "10482.48787536", "last": "117.90", "timestamp": 1368230351.260416, "bid": "117.90", "high": "119.98", "low": "109.20", "ask": "117.95"}
{"volume": "10479.48787536", "last": "117.90", "timestamp": 1368230353.784478, "bid": "117.90", "high": "119.98", "low": "109.20", "ask": "117.95"}
...
```
According to the official JSON specification the double quote delimiters `"` are mandatory, but each tool in the processing chain also accepts entries where single quote delimiters `'` are used. More importantly each of them *produces* tuples with single quote delimiters (due to some implementation details).

The structure of the tuple is arbitrary, except for `timestamp` which is always required. The `volume`, `high` and `low` values are for the last 24 hours; `last`, `bid` and `ask` contain the most recent values.

+ `last`: USD value paid for a Bitcoin in the most recent transactions;
+ `bid`: highest bid price in USD somebody is currently willing pay for a BTC;
+ `ask`: lowest ask prices in USD for which somebody is willing to sell a BTC at;
+ `high`: highest transaction price in USD in the last 24 hours;
+ `low`: lowest transaction price in USD in the last 24 hours;
+ `volume`: number of BTCs traded in the last 24 hours;
+ `timestamp`: UNIX timestamp for current quote;

This composition is true for the initial, unprocessed quote stream: Except for `timestamp` each component can be removed or transformed; also new ones can be calculated and added to the quotes in the stream. In theory it is possible to remove the `timestamp`, but since most of the tools assume its presence it should not be.

## Tool Chain

Let's start with the most basic operation: Asking the exchange for quotes and recording them for later usage into a file. You do this with the `ticker.py` tool:
``` sh
$ ./ticker.py -v > log/ticks.log
```
This tool polls the exchange's ticker URL almost every second and stores the reported quotes in `log/ticks.log`; plus thanks to the `-v` (--verbose) switch the quotes are also printed on the terminal.

Each tool should have a `-h` (--help) switch, printing a short description what it's supposed to do and showing other optional or mandatory arguments. In the ideal case a tool should have optional arguments only, read from the standard input and write to the standard output.

Although not always possible following this philosophy allows for a quick and simple "plumbing" of different tools together in a chain. Mandatory options can in the most cases avoided by using reasonable defaults, e.g.
``` sh
$ ./ticker.py -h
usage: ticker.py [-h] [-v] [-i INTERVAL] [-u URL]

Polls exchange for new ticks: The poll interval limits the maximum possible
tick resolution, so keeping it as low as possible is desired. But since the
exchange does impose a request limit per time unit it's not possible to poll
beyond that cap (without getting banned).

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose logging (default: False)
  -i INTERVAL, --interval INTERVAL
                        seconds between polls (default: 1.25 [s])
  -u URL, --url URL     API (default: https://www.bitstamp.net/api/ticker/)
```

### Cat, Filter, Float, Logarithm, Simulate and Publish

Let's plunge into analyzing the following chain:
``` sh
$ cat log/ticks.log | ./filter.py -e high low -e bid ask -e volume | ./map/float.py -p last -r last | ./map/log.py -p last -r last | ./simulate.py -a 0.001 | ./zmq/pub.py -v > /dev/null
```
It first takes the recorded ticks and prints them via the standard UNIX command `cat` to the standard output. Then in a second step, the `high`, `low`, `bid`, `ask` and `volume` components of each quote are *excluded* using the `filter.py` tool. In the next two steps the `last` value is mapped with `map/float.py` to a floating point number (from a string) and then with `map/log.py` to its logarithmic value.

The `simulate.py` tool ensures that the quote stream flows with a 1000 fold *acceleration* compared to its original real time speed. In this case the stream is actually slowed down, since otherwise without the simulator the tool chain would try  to process the stream as fast as possible, which is not always desirable since in general we'd like to have some CPU power left for other purposes.

Finally, with `zmq/pub.py` the stream is published on the default TCP port `tcp://*:8888`, where it can be subscribed to from a different terminal or even from a different machine (in the same network). With the help of this publisher we can fork a quote stream, and apply different tool chains to each sub-stream.

Since the quotes are now published, we suppress the standard output by wiring it to `/dev/null`. But we still would like to see that the stream is flowing and have therefore the `-v` (--verbose) switch activated. In contrast to the standard output the quotes' timestamps are formatted properly if we use the verbose switch; the actual publication keeps the UNIX timestamp format though!

As a summary, quotes provided to the tool chain as input look like this:
``` json
{"volume": "10482.13511879", "last": "117.80", "timestamp": 1368230343.756902, "bid": "117.15", "high": "119.98", "low": "109.20", "ask": "117.90"}
```
The published output on the TCP port looks like this:
``` json
{"timestamp": 1368230927.929788, "last": [4.768139014266231]}
```
And the output we see on the terminal looks like this:
``` json
[2013-05-11 04:59:03.756901] {"timestamp": 1368230343.756902, "last": [4.768988271217486]}
```
We have thrown away everything we're not interested in and have mapped the `last` component with the *logarithm* function. The reason behind using the logarithm instead of the original value is due to some advantageous mathematical properties.

### Subscribe, Interpolate, Return, Volatility, Alias and Publish

``` sh
$ ./zmq/sub.py | ./interpolate.py -i 1.200 | ./reduce/return.py -p last -r return -n 500 | ./reduce/volatility.py -p return -r volatility -n 500 | ./alias.py -m volatility lhs-volatility | ./zmq/pub.py -pub "tcp://*:7777" -v > /dev/null
```

``` sh
$ ./zmq/sub.py | ./interpolate.py -i 1.000 | ./reduce/return.py -p last -r return -n 600 | ./reduce/volatility.py -p return -r volatility -n 600 | ./alias.py -m volatility rhs-volatility | ./zmq/pub.py -pub "tcp://*:9999" -v > /dev/null
```
### Double Subscribe, Ratio and Publish

``` sh
$ ./zmq/sub.py -sub "tcp://127.0.0.1:7777" -sub "tcp://127.0.0.1:9999" | ./reduce/ratio.py -n lhs-volatility -d rhs-volatility -r ratio | ./zmq/pub.py -pub "tcp://*:7799" -v > /dev/null
```

### Subscribe, Grep and Alias

``` sh
$ ./zmq/sub.py -sub "tcp://127.0.0.1:7799" | grep "rhs-volatility" | ./alias.py -m rhs-volatility volatility -v > data/lrv-ratio.log
```

### Cat, Exponentiate, and Alpha Sim

```
$ cat data/lrv-ratio.log | ./map/exp.py -p last -r price | ./trade/alpha-sim.py -v > data/alpha-sim.log
```
