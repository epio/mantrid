
.. _index:

Mantrid Documentation
=====================

Mantrid is a pure-Python load balancer for large numbers of constantly changing hostnames. It is configured with a REST API, monitors bandwidth and connection statistics, and can temporarily hold connections open while backend servers restart.

It trades some raw speed for flexibility, but is still designed to be fast. Its aim is to have latency of no more than 10ms, and have no more than a 10% reduction in throughput.

It's available on `GitHub <https://github.com/epio/mantrid>`_.


.. toctree::
    :maxdepth: 2

    installation
    running
    configuration_file
    configuring_rules
    actions
    http_api
