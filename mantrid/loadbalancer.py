import eventlet
import logging
import traceback
import mimetools
import resource
from eventlet import wsgi
from eventlet.green import socket
from .actions import Unknown


class Balancer(object):
    """
    Main loadbalancer class.
    """

    nofile = 102400

    def __init__(self, listen_ports, management_port):
        """
        Constructor.

        Takes one parameter, the dict of ports to listen on.
        The key in this dict is the port number, and the value
        is if it's an internal endpoint or not.
        Internal endpoints do not have X-Forwarded-* stripped;
        other ones do, and have X-Forwarded-For added.
        """
        self.listen_ports = listen_ports
        self.management_port = management_port
    
    @classmethod
    def main(cls):
        balancer = cls({80: False}, 8042)
        balancer.run()

    def increase_limits(self):
        # Increase resource limits
        resource.setrlimit(resource.RLIMIT_NOFILE, (self.nofile, self.nofile))
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        assert soft == self.nofile
        assert hard == self.nofile

    def run(self):
        # First, initialise the process
        self.increase_limits()
        from .actions import Proxy
        self.hosts = {
            "localhost": (
                Proxy,
                {"backends": [["127.0.0.1", 8042]]},
                False,
            ),
            "local.ep.io": (
                Proxy,
                {"backends": [["127.0.0.1", 8042]]},
                True,
            ),
        }
        # Then, launch the socket loops
        pool = eventlet.GreenPile(len(self.listen_ports) + 1)
        pool.spawn(self.management_loop, self.management_port)
        for port, internal in self.listen_ports.items():
            pool.spawn(self.listen_loop, port, internal)
        # Wait for one to exit, or for a clean/forced shutdown
        try:
            pool.next()
        except (KeyboardInterrupt, StopIteration, SystemExit):
            return
        except:
            # The main loop died with an exception
            logging.error(traceback.format_exc())
            return
        else:
            # If any loop dies, kill the entire process
            return
        # We're done
        logging.info("Exiting")

    ### Management ###

    def management_loop(self, port):
        """
        Accepts management requests.
        """
        sock = eventlet.listen(("::", port), socket.AF_INET6)
        logging.info("Listening for management on port %i" % port)
        with open("/dev/null", "w") as log_dest:
            wsgi.server(
                sock,
                self.handle_management,
                log = log_dest,
            )
    
    def handle_management(self, environ, start_response):
        """
        Handles a management port request. WSGI function.
        """
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['Hello, Boss!\r\n']

    ### Client handling ###

    def listen_loop(self, port, internal=False):
        """
        Accepts incoming connections.
        """
        sock = eventlet.listen(("::", port), socket.AF_INET6)
        logging.info("Listening for requests on port %i" % port)
        eventlet.serve(
            sock,
            lambda sock, addr: self.handle(sock, addr, internal),
            concurrency = 10000,
        )

    def resolve_host(self, host):
        # Check for an exact or any subdomain matches
        bits = host.split(".")
        for i in range(len(bits)):
            subhost = ".".join(bits[i:])
            if subhost in self.hosts:
                action, kwargs, allow_subs = self.hosts[subhost]
                if allow_subs or i == 0:
                    return action(host=host, **kwargs)
        return Unknown(host)

    def handle(self, sock, address, internal=False):
        """
        Handles an incoming HTTP connection.
        """
        try:
            rfile = sock.makefile('rb', 4096)
            # Read the first line
            first = rfile.readline().strip("\r\n")
            words = first.split()
            # Ensure it looks kind of like HTTP
            if not (2 <= len(words) <= 3):
                self.send_error(sock, 400, "Bad request syntax (%r)" % first)
                return
            path = words[1]
            # Read the headers
            headers = mimetools.Message(rfile, 0)
            # Work out the host
            host = headers['Host']
            headers['Connection'] = "close"
            if not internal:
                headers['X-Forwarded-For'] = address[0]
                headers['X-Forwarded-Protocol'] = ""
            # Make sure they're not using odd encodings
            if "Transfer-Encoding" in headers:
                self.send_error(sock, 411, "Length Required")
                return
            # Match the host to an action
            action = self.resolve_host(host)
            # Run the action
            rfile._rbuf.seek(0)
            action.handle(
                sock = sock,
                read_data = first + "\r\n" + str(headers) + "\r\n" + rfile._rbuf.read(),
                path = path,
                headers = headers,
            )
        except socket.error, e:
            if e.errno != 32:
                logging.error(traceback.format_exc())
        except:
            logging.error(traceback.format_exc())
            try:
                sock.sendall("HTTP/1.0 500 Internal Server Error\r\n\r\nThere has been an internal error in the load balancer.")
            except socket.error, e:
                if e.errno != 32:
                    raise
        finally:
            try:
                sock.close()
                rfile.close()
            except:
                logging.error(traceback.format_exc())

if __name__ == "__main__":
    Balancer.main()
