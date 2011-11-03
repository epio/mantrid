Guide: A Simple Setup
=====================

This guide will show you how to get a very simple Mantrid install working - we'll have one host, which we proxy through to a backend, and then we'll show you how to put it into "spin" mode (where it will hold open incoming connections) and then back into proxy mode, which will then let all the pending connections through.

First of all, install Mantrid; instructions on how to do this are on :doc:`the main page </index>`. Once you have it installed, you need to start Mantrid::

    sudo mantrid

Now Mantrid should be listening on port 80, and listening for management connections on localhost:8042. If you go to http://localhost/ now, you should get a simple page telling you that you currently have no hosts.

A single host
-------------

Let's add an example host - we'll just use "localhost" for now, and tell it to proxy to ``google.com``::

    mantrid-client set localhost proxy true backends=localhost:8000

That tells the client to set a new rule, for the domain ``localhost``, using the action ``proxy``, handling subdomains as well (``true``), and then specifies the one backend we're using - in this case, we're presuming you're running something on port 8000 locally - change that as required.

If you now go to http://localhost/, you should see the application you redirected to appear.

Holding back connections
------------------------

Now, let's change localhost to 'spin' incoming connections::

    mantrid-client set localhost spin true

(spin takes no arguments, so there is nothing after ``true``).

If you now visit http://localhost/, your browser will just sit and try and load the page - Mantrid is holding open connections (this is useful if, for example, you are restarting your web servers). Now, you can set it back to proxy mode::

    mantrid-client set localhost proxy true backends=localhost:8000

Your open connection will then successfully go through and serve the page you saw before.

Multiple backends
-----------------

You can also set more than one backend; if we set::

    mantrid-client set localhost proxy true backends=localhost:8000,localhost:8001

then hitting http://localhost/ will randomly connect you through to one of the two ports.
