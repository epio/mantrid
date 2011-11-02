import eventlet
import errno
import logging
import traceback
import mimetools
import resource
import json
import os
import sys
import argparse
from eventlet import wsgi
from eventlet.green import socket
from .actions import Unknown, Proxy, Empty, Static, Redirect, NoHosts, Spin
from .config import SimpleConfig
from .management import ManagementApp
from .stats_socket import StatsSocket
from .greenbody import GreenBody


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
        "no_hosts": NoHosts,
    }

    def __init__(self, external_addresses, internal_addresses, management_addresses, state_file, uid=None, gid=65535, static_dir="/etc/mantrid/static/"):
        """
        Constructor.

        Takes one parameter, the dict of ports to listen on.
        The key in this dict is the port number, and the value
        is if it's an internal endpoint or not.
        Internal endpoints do not have X-Forwarded-* stripped;
        other ones do, and have X-Forwarded-For added.
        """
        self.external_addresses = external_addresses
        self.internal_addresses = internal_addresses
        self.management_addresses = management_addresses
        self.state_file = state_file
        self.uid = uid
        self.gid = gid
        self.static_dir = static_dir

    @classmethod
    def main(cls):
        # Parse command-line args
        parser = argparse.ArgumentParser(description='The Mantrid load balancer')
        parser.add_argument('--debug', dest='debug', action='store_const', const=True, help='Enable debug logging')
        parser.add_argument('-c', '--config', dest='config', default=None, metavar="PATH", help='Path to the configuration file')
        args = parser.parse_args()
        # Set up logging
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
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
        # Load settings from the config file
        if args.config is None:
            if os.path.exists("/etc/mantrid/mantrid.conf"):
                args.config = "/etc/mantrid/mantrid.conf"
                logging.info("Using configuration file %s" % args.config)
            else:
                args.config = "/dev/null"
                logging.info("No configuration file found - using defaults.")
        else:
            logging.info("Using configuration file %s" % args.config)
        config = SimpleConfig(args.config)
        balancer = cls(
            config.get_all_addresses("bind", set([(("::", 80), socket.AF_INET6)])),
            config.get_all_addresses("bind_internal"),
            config.get_all_addresses("bind_management", set([(("127.0.0.1", 8042), socket.AF_INET), (("::1", 8042), socket.AF_INET6)])),
            config.get("state_file", "/var/lib/mantrid/state.json"),
            config.get_int("uid", 4321),
            config.get_int("gid", 4321),
            config.get("static_dir", "/etc/mantrid/static/"),
        )
        balancer.run()

    def load(self):
        "Loads the state from the state file"
        try:
            if os.path.getsize(self.state_file) <= 1:
                raise IOError("File is empty.")
            with open(self.state_file) as fh:
                state = json.load(fh)
                assert isinstance(state, dict)
                self.hosts = state['hosts']
                self.stats = state['stats']
            for key in self.stats:
                self.stats[key]['open_requests'] = 0
        except (IOError, OSError):
            # There is no state file; start empty.
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
        # Try to ensure the state file is readable
        state_dir = os.path.dirname(self.state_file)
        if not os.path.isdir(state_dir):
            os.makedirs(state_dir)
        if self.uid is not None:
            try:
                os.chown(state_dir, self.uid, -1)
            except OSError:
                pass
            try:
                os.chown(self.state_file, self.uid, -1)
            except OSError:
                pass
        # Then, launch the socket loops
        pool = GreenBody(
            len(self.external_addresses) +
            len(self.internal_addresses) +
            len(self.management_addresses) +
            1
        )
        pool.spawn(self.save_loop)
        for address, family in self.external_addresses:
            pool.spawn(self.listen_loop, address, family, internal=False)
        for address, family in self.internal_addresses:
            pool.spawn(self.listen_loop, address, family, internal=True)
        for address, family in self.management_addresses:
            pool.spawn(self.management_loop, address, family)
        # Give the other threads a chance to open their listening sockets
        eventlet.sleep(0.5)
        # Drop to the lesser UID/GIDs, if supplied
        if self.gid:
            try:
                os.setegid(self.gid)
                os.setgid(self.gid)
            except OSError:
                logging.error("Cannot change to GID %i (probably not running as root)" % self.gid)
            else:
                logging.info("Dropped to GID %i" % self.gid)
        if self.uid:
            try:
                os.seteuid(0)
                os.setuid(self.uid)
                os.seteuid(self.uid)
            except OSError:
                logging.error("Cannot change to UID %i (probably not running as root)" % self.uid)
            else:
                logging.info("Dropped to UID %i" % self.uid)
        # Ensure we can save to the state file, or die hard.
        try:
            open(self.state_file, "a").close()
        except (OSError, IOError):
            logging.critical("Cannot write to state file %s" % self.state_file)
            sys.exit(1)
        # Wait for one to exit, or for a clean/forced shutdown
        try:
            pool.wait()
        except (KeyboardInterrupt, StopIteration, SystemExit):
            pass
        except:
            logging.error(traceback.format_exc())
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

    def management_loop(self, address, family):
        """
        Accepts management requests.
        """
        try:
            sock = eventlet.listen(address, family)
        except socket.error, e:
            logging.critical("Cannot listen on (%s, %s): %s" % (address, family, e))
            return
        # Sleep to ensure we've dropped privileges by the time we start serving
        eventlet.sleep(0.5)
        # Actually serve management
        logging.info("Listening for management on %s" % (address, ))
        management_app = ManagementApp(self)
        with open("/dev/null", "w") as log_dest:
            wsgi.server(
                sock,
                management_app.handle,
                log = log_dest,
            )

    ### Client handling ###

    def listen_loop(self, address, family, internal=False):
        """
        Accepts incoming connections.
        """
        try:
            sock = eventlet.listen(address, family)
        except socket.error, e:
            if e.errno == errno.EADDRINUSE:
                logging.critical("Cannot listen on (%s, %s): already in use" % (address, family))
                raise
            elif e.errno == errno.EACCES and address[1] <= 1024:
                logging.critical("Cannot listen on (%s, %s) (you might need to launch as root)" % (address, family))
                return
            logging.critical("Cannot listen on (%s, %s): %s" % (address, family, e))
            return
        # Sleep to ensure we've dropped privileges by the time we start serving
        eventlet.sleep(0.5)
        # Start serving
        logging.info("Listening for requests on %s" % (address, ))
        eventlet.serve(
            sock,
            lambda sock, addr: self.handle(sock, addr, internal),
            concurrency = 10000,
        )

    def resolve_host(self, host, protocol="http"):
        # Special case for empty hosts dict
        if not self.hosts:
            return NoHosts(self, host, "unknown")
        # Check for an exact or any subdomain matches
        bits = host.split(".")
        for i in range(len(bits)):
            for prefix in ["%s://" % protocol, ""]:
                subhost = prefix + (".".join(bits[i:]))
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
                host = "unknown"
            headers['Connection'] = "close"
            if not internal:
                headers['X-Forwarded-For'] = address[0]
                headers['X-Forwarded-Protocol'] = ""
                headers['X-Forwarded-Proto'] = ""
            # Make sure they're not using odd encodings
            if "Transfer-Encoding" in headers:
                sock.sendall("HTTP/1.0 411 Length Required\r\nConnection: close\r\nContent-length: 0\r\n\r\n")
                return
            # Match the host to an action
            protocol = "http"
            if headers.get('X-Forwarded-Protocol', headers.get('X-Forwarded-Proto', "")).lower() in ("ssl", "https"):
                protocol = "https"
            action = self.resolve_host(host, protocol)
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
            if e.errno not in (errno.EPIPE, errno.ETIMEDOUT, errno.ECONNRESET):
                logging.error(traceback.format_exc())
        except:
            logging.error(traceback.format_exc())
            try:
                sock.sendall("HTTP/1.0 500 Internal Server Error\r\n\r\nThere has been an internal error in the load balancer.")
            except socket.error, e:
                if e.errno != errno.EPIPE:
                    raise
        finally:
            try:
                sock.close()
                rfile.close()
            except:
                logging.error(traceback.format_exc())

if __name__ == "__main__":
    Balancer.main()
