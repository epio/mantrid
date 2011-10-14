Running Mantrid
===============


Quick Start
-----------

To run Mantrid with a default configuration, just run::

    sudo mantrid

(or just run ``mantrid`` as root). Mantrid needs root in order to bind to port 80 and set its resource limits; it will automatically drop to a less-privileged user once it has finished starting up.

The default configuration is to serve external clients on port 80 (from all available addresses), and to have management on port 8042, bound to localhost only.


Configuration
-------------

Mantrid will look for startup configuration in /etc/mantrid/mantrid.conf by default, or you can specify the location on the command line::

    mantrid -c /home/andrew/mantrid.conf

The configuration file is in the format ``variable_name = value``; comments are denoted by starting them with a ``#``. For available configuration options, see the :doc:`configuration_file` page.

Note that the configuration file only tells Mantrid how to start up; configuring hostnames and Mantrid's responses to them can only be done via the HTTP API (there is a ``mantrid-client`` tool available to make this easier for simple scenarios). For more information, read :doc:`configuring_rules`.


Running as a normal user
------------------------

If you only make Mantrid listen on port 1024 or greater, there is no need to run it as root, unless you wish to take advantage of the automatic resource limit changes (you can change resource limits on your system manually as well; see system-specific documentation on things like ``ulimit`` or ``pam_limits``).

