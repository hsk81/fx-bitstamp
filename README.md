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

Now, it's time to aplly some advanced operations:
``` sh
$ ./zmq/sub.py | ./interpolate.py -i 1.200 | ./reduce/return.py -p last -r return -n 500 | ./reduce/volatility.py -p return -r volatility -n 500 | ./alias.py -m volatility lhs-volatility | ./zmq/pub.py -pub "tcp://*:7777" -v > /dev/null ## "*" implies on any IP address
```
With `zmq/sub.py` we subscribe to the previously published stream by default assumed to be on the *local* machine at `tcp://127.0.0.1:8888`.

Then we create with `interpolate.py` a homogeneous time series by sampling the stream every 1.2 seconds. Inhomogeneous to homogeneous time series conversion is a big subject in algorithmic trading, because many of the higher level operators assume a homogeneous interval between each quote in the stream. But this is only achievable via interpolation: The current implementation simply takes the most recent tick for an interpolated quote and does not try something more advanced like a linear interpolation.

Once we have a homogeneous stream, we calculate for each quote with `reduce/return.py` *overlapping* returns of the last corresponding 10 minutes (500 * 1.2 seconds). Calculating returns basically centers the time series around zero and plots only the consecutive (but overlapping) differences.

Based on the returns we can now calculate with `reduce/volatility.py` the activity for each 10 minute window of the quote stream. By default the so called *annualized volatility* is delivered. Once the calculation is done, we *move* (rename) the `volatility` component with `alias.py` to `lhs-volatility` (to avoid later a name clash).

Finally we publish the stream again in a similar fashion like before; except this time we need to use the non default port `7777`, since the default has already been used.

Second volatility calculation:
``` sh
$ ./zmq/sub.py | ./interpolate.py -i 1.000 | ./reduce/return.py -p last -r return -n 600 | ./reduce/volatility.py -p return -r volatility -n 600 | ./alias.py -m volatility rhs-volatility | ./zmq/pub.py -pub "tcp://*:9999" -v > /dev/null ## "*" implies on any IP address
```
For reasons to explained later we *repeat* the previous calculation, but this time our interpolation interval is 1.0 second, and we store the volatility in `rhs-volatility`. The following image shows the effect of changing the interpolation interval and calculating the corresponding volatilities:

![Volatility Plot](http://db.tt/Vo7Ls9tp "Logarithms, Returns and Volatilities")

The plot shows the logarithm, return and volatility for *three* different interpolation interval values: Two of them are similar, but one is quite distinct. The observed effect is an apparent shift relative to each other. This makes sense since the larger the interpolation interval, the fewer the number of homogeneous ticks (since we sample less), and therefore the corresponding curves lag behind the ones with the smaller interpolation intervals.

### Double Subscribe, Ratio and Publish

So we have now *two* volatility time series, and would like to bring them together:
``` sh
$ ./zmq/sub.py -sub "tcp://127.0.0.1:7777" -sub "tcp://127.0.0.1:9999" | ./reduce/ratio.py -n lhs-volatility -d rhs-volatility -r ratio | ./zmq/pub.py -pub "tcp://*:7799" -v > /dev/null ## "*" implies on any IP address
```
First with `zmq/sub.py` we subscribe to *both* streams at `tcp://127.0.0.1:7777` and `tcp://127.0.0.1:9999`: The subscription is fair in the sense that it tries to take alternatively from each input queue as long as each queue has a quote to deliver.

The `reduce/ratio.py` divides the `lhs-volatility` with `rhs-volatility` values; since these two volatilities are slightly off from each other (due to different interpolations), we actually end up calculating a **trend indicator**: If the ratio is higher than one we have a positive or negative trend, if it hovers around one there is no trend, and if it is less then one then we should observe a mean reverting behavior. The following figure shows this quite clearly:

![Ratio Plot](http://db.tt/iDQNvyLK "USD Price (B), Log Returns (R), PnL Percent (C), Volatility Ratio (M), BTC & USD Account (M&Y), Volatility (G)")

The figure shows a period of about 30 days, and has the following sub-plots charted:

+ The `blue` plot shows the original price for Bitcoins denominated in US dollars; the `red` plot show the logarithmic returns of the price; the `cyan` plot and the plot immediately below it with the two `magenta` and `yellow` plots show the performance and behavior of of a trading strategy which is based on the volatility ratio and which we'll analyze in detail below; the `magenta` plot (2nd column and row) shows the volatility ratio: it's not extremely clear cut, but when you look at the peaks which are above the value of 2.0 then you can observe  in most cases also a corresponding trend in the original price; the `green` plot displays the price volatility.

Once the trend indicator (named simply as `ratio`) is calculated, we publish it with `zmq/pub.py` on the port `7799` and print verbosely the current stream on the terminal.

### Subscribe, Grep and Alias

``` sh
$ ./zmq/sub.py -sub "tcp://127.0.0.1:7799" | grep "rhs-volatility" | ./alias.py -m rhs-volatility volatility -v > data/lrv-ratio.log
```

### Cat, Exponentiate, and Alpha Sim

```
$ cat data/lrv-ratio.log | ./map/exp.py -p last -r price | ./trade/alpha-sim.py -v > data/alpha-sim.log
```
