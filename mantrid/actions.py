"""
Contains Mantrid's built-in actions.
"""

import errno
import os
import random
import eventlet
from eventlet.green import socket
from httplib import responses
from .socketmeld import SocketMelder


class Action(object):
    "Base action. Doesn't do anything."

    def __init__(self, balancer, host, matched_host):
        self.host = host
        self.balancer = balancer
        self.matched_host = matched_host

    def handle(self, sock, read_data, path, headers):
        raise NotImplementedError("You must use an Action subclass")


class Empty(Action):
    "Sends a code-only HTTP response"

    code = None

    def __init__(self, balancer, host, matched_host, code):
        super(Empty, self).__init__(balancer, host, matched_host)
        self.code = code

    def handle(self, sock, read_data, path, headers):
        "Sends back a static error page."
        try:
            sock.sendall("HTTP/1.0 %s %s\r\nConnection: close\r\nContent-length: 0\r\n\r\n" % (self.code, responses.get(self.code, "Unknown")))
        except socket.error, e:
            if e.errno != errno.EPIPE:
                raise


class Static(Action):
    "Sends a static HTTP response"

    type = None

    def __init__(self, balancer, host, matched_host, type=None):
        super(Static, self).__init__(balancer, host, matched_host)
        if type is not None:
            self.type = type

    def handle(self, sock, read_data, path, headers):
        "Sends back a static error page."
        assert self.type is not None
        try:
            try:
                with open(os.path.join(self.balancer.static_dir, "%s.http" % self.type)) as fh:
                    sock.sendall(fh.read())
            except IOError:
                with open(os.path.join(os.path.dirname(__file__), "static", "%s.http" % self.type)) as fh:
                    sock.sendall(fh.read())
        except socket.error, e:
            if e.errno != errno.EPIPE:
                raise


class Unknown(Static):
    "Standard class for 'nothing matched'"

    type = "unknown"


class NoHosts(Static):
    "Standard class for 'there are no host entries at all'"

    type = "no-hosts"


class Redirect(Action):
    "Sends a redirect"

    type = None

    def __init__(self, balancer, host, matched_host, redirect_to):
        super(Redirect, self).__init__(balancer, host, matched_host)
        self.redirect_to = redirect_to

    def handle(self, sock, read_data, path, headers):
        "Sends back a static error page."
        if "://" not in self.redirect_to:
            destination = "http%s://%s" % (
                "s" if headers.get('X-Forwarded-Protocol', headers.get('X-Forwarded-Proto', "")).lower() in ("https", "ssl") else "",
                self.redirect_to
            )
        else:
            destination = self.redirect_to
        try:
            sock.sendall("HTTP/1.0 302 Found\r\nLocation: %s/%s\r\n\r\n" % (
                destination.rstrip("/"),
                path.lstrip("/"),
            ))
        except socket.error, e:
            if e.errno != errno.EPIPE:
                raise


class Proxy(Action):
    "Proxies them through to a server. What loadbalancers do."

    attempts = 1
    delay = 1

    def __init__(self, balancer, host, matched_host, backends, attempts=None, delay=None):
        super(Proxy, self).__init__(balancer, host, matched_host)
        self.backends = backends
        assert self.backends
        if attempts is not None:
            self.attempts = int(attempts)
        if delay is not None:
            self.delay = float(delay)

    def handle(self, sock, read_data, path, headers):
        "Sends back a static error page."
        for i in range(self.attempts):
            try:
                server_sock = eventlet.connect(
                    tuple(random.choice(self.backends)),
                )
            except socket.error:
                eventlet.sleep(self.delay)
                continue
            # Function to help track data usage
            def send_onwards(data):
                server_sock.sendall(data)
                return len(data)
            try:
                size = send_onwards(read_data)
                size += SocketMelder(sock, server_sock).run()
            except socket.error, e:
                if e.errno != errno.EPIPE:
                    raise


class Spin(Action):
    """
    Just holds the request open until either the timeout expires, or
    another action becomes available.
    """

    timeout = 120
    check_interval = 1

    def __init__(self, balancer, host, matched_host, timeout=None, check_interval=None):
        super(Spin, self).__init__(balancer, host, matched_host)
        if timeout is not None:
            self.timeout = int(timeout)
        if check_interval is not None:
            self.check_interval = int(check_interval)

    def handle(self, sock, read_data, path, headers):
        "Just waits, and checks for other actions to replace us"
        for i in range(self.timeout // self.check_interval):
            # Sleep first
            eventlet.sleep(self.check_interval)
            # Check for another action
            action = self.balancer.resolve_host(self.host)
            if not isinstance(action, Spin):
                return action.handle(sock, read_data, path, headers)
        # OK, nothing happened, so give up.
        action = Static(self.balancer, self.host, self.matched_host, type="timeout")
        return action.handle(sock, read_data, path, headers)
