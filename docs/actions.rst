Actions
=======

Actions are what you build rules with in Mantrid - they cover all the tasks from returning error pages to proxying requests through to a backend (as you'd expect a load balancer to do).

Each action has zero or more configuration options - where no table of options is shown, the action in question takes no configuration options.


empty
-----

.. table:: 

    ========  ========  ===========
    Argument  Required  Description
    ========  ========  ===========
    code      Yes       The (numeric) HTTP code to send as a response
    ========  ========  ===========

Sends a HTTP response with a zero-length body (literally just the status code and response headers).


proxy
-----

.. table:: 

    ========    ========  ===========
    Argument    Required  Description
    ========    ========  ===========
    backends    Yes       A list of backend servers to use
    attempts    No        How many times a connection is attempted to the backends. Defaults to 1.
    delay       No        Delay between attempts, in seconds. Defaults to 1.
    ========    ========  ===========

Proxies the request through to a backend server. Will randomly choose a server from those provided as "backends"; provides no session stickiness.

If a connection to a backend drops, it can optionally retry several times with a delay until it gets a response. If no connection is ever accomplished, will send the ``timeout`` static page.


redirect
--------

.. table:: 

    ===========    ========  ===========
    Argument       Required  Description
    ===========    ========  ===========
    redirect_to    Yes       The URL to redirect to.
    ===========    ========  ===========

Sends a HTTP 302 Found response redirecting the user to a different URL. If the URL specified has the protocol part included, they will be forced onto that protocol; otherwise, they will be forwarded with the same protocol (http or https) that they are currently using.

Note that the use of HTTPS is detected by the presence of an ``X-Forwarded-Proto`` or ``X-Forwarded-Protocol`` header on a ``bind_internal`` interface. Mantrid cannot do SSL termination itself.


spin
----

.. table:: 

    ==============  ========  ===========
    Argument        Required  Description
    ==============  ========  ===========
    timeout         No        How long to wait before giving up, in seconds. Defaults to 120.
    check_interval  No        Delay between rule checks, in seconds. Defaults to 1.
    ==============  ========  ===========

Holds the incoming request open, checking Mantrid's rules table periodically for a match. If a new rule is added matching the hostname while the request is being held open, Mantrid will then pass control over to the new action. If no new rule is added before the timeout expires, sends the ``timeout`` static response.

This is particularly useful for webservers that are being started or restarted; you can set the site to ``spin``, restart the webserver (knowing that your requests are being held), and then set the rule back to ``proxy`` again and all the requests will continue as normal.


static
------

.. table:: 

    ========  ========  ===========
    Argument  Required  Description
    ========  ========  ===========
    type      Yes       The name of the static response to send, without the ``.http`` extension.
    ========  ========  ===========

Sends a HTTP response that is already saved as a file on disk. Mantrid ships with several default responses, but you can provide your own in the directory specified by the ``static_dir`` configuration option.

Default responses:

 * ``no-hosts``, used by the ``no_hosts`` action (short message for a fresh mantrid install)
 * ``test``, a short test page that says "Congratulations!...".
 * ``timeout``, used by the ``spin`` and ``proxy`` actions after a timeout.
 * ``unknown``, used by the ``unknown`` action.


no_hosts
--------

Sends a predefined response pointing out that the load balancer has no hosts configured at all. The default action if the server is completely devoid of rules (as it would be on a fresh install).


unknown
-------

Sends a predefined response that says "The site you have tried to access is not known to this server". The default action for any unknown host; takes no arguments. It is unlikely you would want to set this as part of a rule.


