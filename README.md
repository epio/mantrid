Mantrid
=======

Mantrid is a pure-Python load balancer for large numbers of constantly changing hostnames. It is configured with a REST API, monitors bandwidth and connection statistics, and can temporarily hold connections open while backend servers restart.

It trades some raw speed for flexibility, but is still designed to be fast. Its aim is to have latency of no more than 10ms, and have no more than a 10% reduction in throughput.

Compatibility
-------------

Mantrid is designed to work with Python 2.6 or 2.7, and requires a Python implementation that supports greenlets (so either CPython or PyPy 1.7 and up).

Quick start
-----------

Install Mantrid:

    $ sudo python setup.py install

Launch Mantrid with the default settings (listening on port 80, management on 8042):

    $ sudo mantrid

Add a host:

    $ mantrid-client set localhost static false type=test

Then visit http://localhost/ to see the test page.


Configuration
-------------

Mantrid is partially configured using a small configuration file (/etc/mantrid/mantrid.conf) which sets up basic things like ports to listen on. The hostnames and load balancing rules are configured at runtime using a HTTP API.

A command-line interface, `mantrid-client`, ships with Mantrid to make simple interactions with the API easier.

Contributing
------------

Mantrid is released under a BSD (3-clause) license. Contributions are very welcome.

