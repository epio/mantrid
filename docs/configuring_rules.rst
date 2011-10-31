Configuring rules
=================

All configuration of Mantrid's load-balancing rules is done at runtime, using the HTTP API (either directly, or via the ``mantrid-client`` command line tool). For simplicity, this document will just demonstrate using the command-line client.

Mantrid only works on the basis of hostnames; for each incoming request, it will take its hostname and attempt to resolve it to an *action*. It will first try and find an exact match to the hostname, and if no match is found it will then keep removing the first part of the hostname (up to the first ``.``) until it has consumed the entire hostname.

Partial matches will only occur if the domain that is eventually partially matched allows subdomain matches.

For example, if we asked for the host "www.andrew.example.com", Mantrid would try to find rules matching these hostnames (in order)::

    www.andrew.example.com
    andrew.example.com
    example.com
    com

If there was an entry for ``andrew.example.com`` with subdomain matches allowed, this would match; however, if only exact matches were allowed, this would not match that entry.

Each rule is made up of three parts: an :doc:`action name <actions>`, arguments for that action (as keywords), and the "are subdomain matches allowed" flag. You can read about the :doc:`actions` and see what options you have.

All changes made via the API take effect immediately, for all future requests.


Adding/Updating a rule
----------------------

Adding and updating a rule are the same operation, called 'set'; if there's a previous record for the hostname you're setting, it will be overwritten. To add a rule that just returns an empty 403 Forbidden to everyone requesting "top-secret.com", or any subdomains, you would call::

    mantrid-client set top-secret.com empty true code=403

The arguments are, in order, the host name (``top-secret.com``), the action name (``empty``), the subdomains_allowed flag (``true``), and the arguments (``code=403``, to tell the empty action what status code to use).


Deleting a rule
---------------

Deleting a rule is pretty simple::

    mantrid-client delete top-secret.com


Listing rules
-------------

You can get a human-readable list of rules using::

    mantrid-client list

This produces something like the following::

    HOST                                ACTION                    SUBDOMS 
    top-secret.com                      empty<403>                True    
    www.forever.com                     spin                      True
