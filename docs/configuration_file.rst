The configuration file
======================

This file is looked for at either ``/etc/mantrid/mantrid.conf`` or the location passed on the command line using the ``-c`` switch.

The default settings would look like this::

    bind = 0.0.0.0:80
    bind_management = 127.0.0.1:8042
    state_file = /var/lib/mantrid/state.json
    uid = 4321
    gid = 4321

Options
-------

bind
~~~~

Tells Mantrid to bind to the given address and port to serve external users. Use the address 0.0.0.0 to listen on all available addresses.

This option may be specified more than once to listen on multiple ports or addresses.


bind_internal
~~~~~~~~~~~~~

Tells Mantrid to bind to the given address and port to serve internal proxies. Use the address 0.0.0.0 to listen on all available addresses.

Requests from internal proxies will not have their ``X-Forwarded-For`` and ``X-Forwarded-Protocol`` headers removed; 'internal' bind addresses are for use behind an SSL terminator, which should add these headers itself.

This option may be specified more than once to listen on multiple ports or addresses.


bind_management
~~~~~~~~~~~~~~~

Tells Mantrid to bind to the given address and port to serve management API requests. Use the address 0.0.0.0 to listen on all available addresses.

Note that there is no authentication on the Mantrid management API; anyone who can access the port can wipe your loadbalancer. We suggest you limit it to either local connections only or a secure subnet.

This option may be specified more than once to listen on multiple ports or addresses.


state_file
~~~~~~~~~~

Specifies the location where Mantrid stores its state between restarts. Defaults to ``/var/lib/mantrid/state.json``. Should be writable by the user Mantrid drops priviledges to; it will attempt to make that possible if it has root access when it is launched.


uid
~~~

The UID to drop to once Mantrid has started. Defaults to 4321.


gid
~~~

The GID to drop to once Mantrid has started. Defaults to 4321.
