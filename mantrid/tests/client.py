import unittest
import eventlet
import socket
from ..loadbalancer import Balancer
from ..client import MantridClient


class MockSocket(object):
    "Fake Socket class that remembers what was sent"

    def __init__(self):
        self.data = ""

    def send(self, data):
        self.data += data
        return len(data)
    
    def sendall(self, data):
        self.data += data


class ClientTests(unittest.TestCase):
    """
    Tests that the client/API work correctly.
    """

    next_port = 30200

    def setUp(self):
        self.__class__.next_port += 3
        self.balancer = Balancer(
            [(("0.0.0.0", self.next_port), socket.AF_INET)],
            [(("0.0.0.0", self.next_port + 1), socket.AF_INET)],
            [(("0.0.0.0", self.next_port + 2), socket.AF_INET)],
            "/tmp/mantrid-test-state",
        )
        self.balancer_thread = eventlet.spawn(self.balancer.run)
        eventlet.sleep(0.1)
        self.client = MantridClient("http://127.0.0.1:%i" % (self.next_port + 2))
    
    def tearDown(self):
        self.balancer.running = False
        eventlet.sleep(0.1)

    def test_set_single(self):
        "Sets a single host"
        # Check we start empty
        self.assertEqual(
            {},
            self.balancer.hosts,
        )
        self.assertEqual(
            {},
            self.balancer.stats,
        )
        # Add a single host
        self.client.set("test-host.com", ["spin", {}, False])
        # See if we got it
        self.assertEqual(
            {"test-host.com": ["spin", {}, False]},
            self.balancer.hosts,
        )
        self.assertEqual(
            {"test-host.com": {}},
            self.balancer.stats,
        )
        # Override with new settings
        self.client.set("test-host.com", ["unknown", {}, True])
        self.assertEqual(
            {"test-host.com": ["unknown", {}, True]},
            self.balancer.hosts,
        )
        self.assertEqual(
            {"test-host.com": {}},
            self.balancer.stats,
        )
        # Try a wrong setting
        self.assertRaises(
            IOError,
            self.client.set, "test-host.com", ["do-da-be-dee", {}, "bruce"],
        )
        # Delete it
        self.client.delete("test-host.com")
        self.assertEqual(
            {},
            self.balancer.hosts,
        )
        self.assertEqual(
            {},
            self.balancer.stats,
        )

    def test_set_multiple(self):
        "Sets a single host"
        # Check we start empty
        self.assertEqual(
            {},
            self.balancer.hosts,
        )
        self.assertEqual(
            {},
            self.balancer.stats,
        )
        # Add multiple hosts
        hosts = {
            "kittens.com": ["spin", {}, False],
            "khaaaaaaaaaan.com": ["unknown", {}, True],
        }
        self.client.set_all(hosts)
        self.assertEqual(
            hosts,
            self.balancer.hosts,
        )
        self.assertEqual(
            {"kittens.com": {}, "khaaaaaaaaaan.com": {}},
            self.balancer.stats,
        )
        # Change to a different set of hosts
        hosts = {
            "ceilingcat.net": ["spin", {}, False],
            "khaaaaaaaaaan.com": ["unknown", {}, True],
        }
        self.client.set_all(hosts)
        self.assertEqual(
            hosts,
            self.balancer.hosts,
        )
        self.assertEqual(
            {"ceilingcat.net": {}, "khaaaaaaaaaan.com": {}},
            self.balancer.stats,
        )
