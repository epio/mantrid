This is Mantrid, a pure-Python load balancer designed for environments with large numbers of constantly-changing hostnames.

It trades some raw speed for flexibility, but is still designed to be fast; the aim is to have latency of no more than 10ms, and no more than a 10% reduction in throughput.

COMPATABILITY
=============

Mantrid is designed to work with Python 2.6 or 2.7, and requires a Python implementation that supports greenlets (so either CPython or PyPy 1.7 and up).


CONFIGURATION
=============

Mantrid is partially configured using a small configuration file (/etc/mantrid/mantrid.conf) which sets up basic things like ports to listen on, while the hostnames and load balancing rules are configured at runtime using a HTTP API.

A mantrid-client command-line interface ships with Mantrid to make simple interactions with the API easier.


QUICKSTART
==========

Launch Mantrid with the default settings (listening on port 80, management on 8042):

    sudo mantrid

Add a host:

    mantrid-client set localhost static false type=test

Then visit http://localhost/ to see the test page.


CONTRIBUTING
============

Mantrid is released under a BSD (3-clause) license; we're happy to accept people's changes provided they're reasonably documented and tested.
