"""
Contains Mantrid's built-in actions.
"""

import os
import random
import eventlet
from eventlet.green import socket
from .socketmeld import SocketMelder


class Action(object):
    "Base action. Doesn't do anything."

    def __init__(self, host):
        self.host = host

    def handle(self, sock, read_data, path, headers):
        raise NotImplementedError("You must use an Action subclass")


class Empty(Action):
    "Sends a code-only HTTP response"

    code = 500
    string = "Internal Server Error"

    def __init__(self, host, code=None, string=None):
        super(Empty, self).__init__(host)
        if code is not None:
            self.code = code
            assert string is not None
            self.string = string
    
    def handle(self, sock, read_data, path, headers):
        "Sends back a static error page."
        try:
            sock.sendall("HTTP/1.0 %s %s\r\nConnection: close\r\nContent-length: 0\r\n\r\n" % (self.code, self.string))
        except socket.error, e:
            if e.errno != 32:
                raise


class Static(Action):
    "Sends a static HTTP response"

    type = None

    def __init__(self, host, type=None):
        super(Static, self).__init__(host)
        if type is not None:
            self.type = type
    
    def handle(self, sock, read_data, path, headers):
        "Sends back a static error page."
        assert self.type is not None
        try:
            with open(os.path.join(os.path.dirname(__file__), "errors", "%s.http" % self.type)) as fh:
                sock.sendall(fh.read())
        except socket.error, e:
            if e.errno != 32:
                raise


class Unknown(Static):
    "Standard class for 'nothing matched'"

    type = "unknown"


class Redirect(Action):
    "Sends a redirect"

    type = None

    def __init__(self, host, redirect_to):
        super(Redirect, self).__init__(host)
        self.redirect_to = redirect_to
        assert "://" in self.redirect_to

    def handle(self, sock, read_data, path, headers):
        "Sends back a static error page."
        try:
            sock.sendall("HTTP/1.0 302 Found\r\nLocation: %s/%s\r\n\r\n" % (
                self.redirect_to,
                path.lstrip("/"),
            ))
        except socket.error, e:
            if e.errno != 32:
                raise


class Proxy(Action):
    "Proxies them through to a server. What loadbalancers do."

    attempts = 1
    delay = 1

    def __init__(self, host, backends, attempts=None, delay=None):
        super(Proxy, self).__init__(host)
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
                if e.errno != 32:
                    raise
