import eventlet
import logging
import traceback
import mimetools
import resource
import json
import os
import sys
from eventlet import wsgi
from eventlet.green import socket
from .actions import Unknown, Proxy, Empty, Static, Redirect, NoHosts, Spin
from .management import ManagementApp
from .stats_socket import StatsSocket


class Balancer(object):
    """
    Main loadbalancer class.
    """

    nofile = 102400
    save_interval = 10
    action_mapping = {
        "proxy": Proxy,
        "empty": Empty,
        "static": Static,
        "redirect": Redirect,
        "unknown": Unknown,
        "spin": Spin,
    }

    def __init__(self, listen_ports, management_port, state_file):
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
        self.state_file = state_file
    
    @classmethod
    def main(cls):
        # Set up logging
        logger = logging.getLogger()
        logger.setLevel(("--debug" in sys.argv) and logging.DEBUG or logging.INFO)
        # Output to stderr, always
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(
            fmt = "%(asctime)s - %(levelname)8s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        # Check they have root access
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (cls.nofile, cls.nofile))
        except (ValueError, resource.error):
            logging.warning("Cannot raise resource limits (run as root/change ulimits)")
        balancer = cls({80: False}, 8042, "/tmp/mantrid.state")
        balancer.run()

    def load(self):
        "Loads the state from the state file"
        try:
            with open(self.state_file) as fh:
                state = json.load(fh)
                assert isinstance(state, dict)
                self.hosts = state['hosts']
                self.stats = state['stats']
        except IOError:
            # There is no state file; start empty.
            if not os.path.exists(self.state_file):
                self.hosts = {}
                self.stats = {}
 
    def save(self):
        "Saves the state to the state file"
        with open(self.state_file, "w") as fh:
            json.dump({
                "hosts": self.hosts,
                "stats": self.stats,
            }, fh)
    
    def run(self):
        # First, initialise the process
        self.load()
        self.running = True
        # Then, launch the socket loops
        pool = eventlet.GreenPile(len(self.listen_ports) + 2)
        pool.spawn(self.save_loop)
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
        self.running = False
        logging.info("Exiting")

    ### Management ###

    def save_loop(self):
        """
        Saves the state if it has changed.
        """
        last_hash = hash(repr(self.hosts))
        while self.running:
            eventlet.sleep(self.save_interval)
            next_hash = hash(repr(self.hosts))
            if next_hash != last_hash:
                self.save()
                last_hash = next_hash

    def management_loop(self, port):
        """
        Accepts management requests.
        """
        sock = eventlet.listen(("::", port), socket.AF_INET6)
        logging.info("Listening for management on port %i" % port)
        management_app = ManagementApp(self)
        with open("/dev/null", "w") as log_dest:
            wsgi.server(
                sock,
                management_app.handle,
                log = log_dest,
            )

    ### Client handling ###

    def listen_loop(self, port, internal=False):
        """
        Accepts incoming connections.
        """
        try:
            sock = eventlet.listen(("::", port), socket.AF_INET6)
        except socket.error, e:
            if e.errno == 98:
                logging.critical("Cannot listen on port %s" % port)
                return
            elif e.errno == 13 and port <= 1024:
                logging.critical("Cannot listen on port %s (you must launch as root)" % port)
                return
            raise
        logging.info("Listening for requests on port %i" % port)
        eventlet.serve(
            sock,
            lambda sock, addr: self.handle(sock, addr, internal),
            concurrency = 10000,
        )

    def resolve_host(self, host):
        # Special case for empty hosts dict
        if not self.hosts:
            return NoHosts(self, host, "unknown")
        # Check for an exact or any subdomain matches
        bits = host.split(".")
        for i in range(len(bits)):
            subhost = ".".join(bits[i:])
            if subhost in self.hosts:
                action, kwargs, allow_subs = self.hosts[subhost]
                if allow_subs or i == 0:
                    action_class = self.action_mapping[action]
                    return action_class(
                        balancer = self,
                        host = host,
                        matched_host = subhost,
                        **kwargs
                    )
        return Unknown(self, host, "unknown")

    def handle(self, sock, address, internal=False):
        """
        Handles an incoming HTTP connection.
        """
        try:
            sock = StatsSocket(sock)
            rfile = sock.makefile('rb', 4096)
            # Read the first line
            first = rfile.readline().strip("\r\n")
            words = first.split()
            # Ensure it looks kind of like HTTP
            if not (2 <= len(words) <= 3):
                sock.sendall("HTTP/1.0 400 Bad Request\r\nConnection: close\r\nContent-length: 0\r\n\r\n")
                return
            path = words[1]
            # Read the headers
            headers = mimetools.Message(rfile, 0)
            # Work out the host
            try:
                host = headers['Host']
            except KeyError:
                self.send_error(sock, 404, "Not Found")
                return
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
            # Record us as an open connection
            stats_dict = self.stats.setdefault(action.matched_host, {})
            stats_dict['open_requests'] = stats_dict.get('open_requests', 0) + 1
            # Run the action
            try:
                rfile._rbuf.seek(0)
                action.handle(
                    sock = sock,
                    read_data = first + "\r\n" + str(headers) + "\r\n" + rfile._rbuf.read(),
                    path = path,
                    headers = headers,
                )
            finally:
                stats_dict['open_requests'] -= 1
                stats_dict['completed_requests'] = stats_dict.get('completed_requests', 0) + 1
                stats_dict['bytes_sent'] = stats_dict.get('bytes_sent', 0) + sock.bytes_sent
                stats_dict['bytes_received'] = stats_dict.get('bytes_received', 0) + sock.bytes_received
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
