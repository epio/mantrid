REST API
========

Mantrid is configured mainly via a REST API, available on port 8042 by default. All changes are done using HTTP with JSON responses.

Note that a *rule* is always formatted as a triple of ``[action_name, kwargs, match_subdomains]``, where ``action_name`` is a string, ``kwargs`` is a mapping of strings to strings or integers, and ``match_subdomains`` is a boolean.

Statistics are returned as a dictionary with four entries: ``open_requests``, ``completed_requests``, ``bytes_sent``, and ``bytes_received``. The names are reasonably self-explanatory, but note that the two byte measurements are only updated once a request is completed.


/hostname/
----------

GET
~~~

Returns a dictionary with all hostnames and their rules.

PUT
~~~

Accepts a dictionary in the same format that GET produces (hostname: rule)


/hostname/www.somesite.com/
---------------------------

GET
~~~

Returns the rule for this hostname, or None if there is no rule for it currently.

PUT
~~~

Accepts a rule triple to be used for this hostname.

DELETE
~~~~~~

Removes the rule for this hostname.


/stats/
-------

GET
~~~

Returns a dictionary with all hostnames and their statistics.


/stats/www.somesite.com/
------------------------

GET
~~~

Returns the statistics for just the specified hostname.


