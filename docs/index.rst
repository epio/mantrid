
.. _index:

Mantrid Documentation
=====================

Mantrid is a pure-Python load balancer for serving large numbers of constantly changing hostnames. It is configured with a REST API, monitors bandwidth and connection statistics, and can temporarily hold connections open while backend servers restart.

It trades some raw speed for flexibility, but is still designed to be fast. Its aim is to have latency of no more than 10ms, and have no more than a 10% reduction in throughput.

It is available on `GitHub <https://github.com/epio/mantrid>`_.


Installation
------------

If you haven't got `pip <http://www.pip-installer.org/>`_ installed, install it from a system package (``python-pip`` on Ubuntu and Debian) or run::

    $ sudo easy_install pip

Then run::

    $ sudo pip install mantrid

You can improve performance by using PyPy 1.7 or greater. Just use the pypy-specific pip to install it. At the time of writing, PyPy 1.7 is not yet released, but a nightly build will work.


Quick start
-----------

To run Mantrid with a default configuration, just run::

    $ sudo mantrid

(Or run ``mantrid`` as root.) Mantrid needs root in order to bind to port 80 and set its resource limits. It automatically drops to a less privileged user once it has started up.

The default configuration is to serve external clients on port 80 (from all available addresses), and to have management on port 8042 bound to localhost.


Configuration
-------------

Mantrid will look for startup configuration in ``/etc/mantrid/mantrid.conf`` by default. You can specify an alternative location on the command line::

    $ mantrid -c /home/andrew/mantrid.conf

The configuration file is in the format ``variable_name = value`` and comments are denoted by starting them with a ``#``. For available configuration options, see the :doc:`configuration_file` page.

Note that the configuration file only tells Mantrid how to start up; configuring hostnames and Mantrid's responses are done via the REST API. You can use the included ``mantrid-client`` tool to interact with the REST API. For more information, read :doc:`configuring_rules`.

Running as a normal user
------------------------

If you only make Mantrid listen on port 1024 or greater, there is no need to run it as root. Mantrid won't be able to automatically change resource limits as a normal user, but you can do it manually with things like ``ulimit`` or ``pam_limits``.

.. toctree::
    :maxdepth: 2

    configuration_file
    configuring_rules
    actions
    rest_api

