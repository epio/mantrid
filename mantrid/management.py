import json


class HttpNotFound(Exception):
    "Exception raised to pass on a 404 error."
    pass


class HttpMethodNotAllowed(Exception):
    "Exception raised for a valid path but invalid method."
    pass


class ManagementApp(object):
    """
    Management WSGI app for the Mantrid loadbalancer.
    Allows endpoints to be changed via HTTP requests to
    the management port.
    """

    def __init__(self, balancer):
        self.balancer = balancer

    def handle(self, environ, start_response):
        "Main entry point"
        # Pass off to the router
        try:
            handler = self.route(
                environ['PATH_INFO'].lower(),
                environ['REQUEST_METHOD'].lower(),
            )
            if handler is None:
                raise HttpNotFound()
        # Handle errors
        except HttpNotFound:
            start_response('404 Not Found', [('Content-Type', 'application/json')])
            return [json.dumps({"error": "not_found"})]
        except HttpMethodNotAllowed:
            start_response('405 Method Not Allowed', [('Content-Type', 'application/json')])
            return [json.dumps({"error": "method_not_allowed"})]
        # Dispatch to the named method
        response = handler(
            environ['PATH_INFO'].lower(),
        )
        # Send the response
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response)]

    def route(self, path, method):
        # Simple routing for paths
        if path == "/":
            if method == "get":
                return self.get_all
            elif method == "put":
                return self.set_all
            else:
                raise HttpMethodNotAllowed()
        else:
            raise HttpNotFound()

    ### Handling methods ###

    def get_all(self, path):
        return self.balancer.hosts
