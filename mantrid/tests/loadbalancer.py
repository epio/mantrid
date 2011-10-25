from unittest import TestCase
from ..loadbalancer import Balancer
from ..actions import Empty, Unknown, Redirect, Spin, Proxy


class BalancerTests(TestCase):
    "Tests the main load balancer class itself"

    def test_resolution(self):
        "Tests name resolution"
        balancer = Balancer(None, None, None, None)
        balancer.hosts = {
            "localhost": [
                "empty",
                {"code": 402},
                False,
            ],
            "local.ep.io": [
                "spin",
                {},
                True,
            ],
            "http://ep.io": [
                "redirect",
                {"redirect_to": "https://www.ep.io"},
                True,
            ],
            "ep.io": [
                "proxy",
                {"backends": ["0.0.0.0:0"]},
                True,
            ],
        }
        # Test direct name resolution
        self.assertEqual(
            balancer.resolve_host("localhost").__class__,
            Empty,
        )
        self.assertEqual(
            balancer.resolve_host("local.ep.io").__class__,
            Spin,
        )
        self.assertEqual(
            balancer.resolve_host("ep.io").__class__,
            Redirect,
        )
        self.assertEqual(
            balancer.resolve_host("ep.io", "https").__class__,
            Proxy,
        )
        # Test subdomain resolution
        self.assertEqual(
            balancer.resolve_host("subdomain.localhost").__class__,
            Unknown,
        )
        self.assertEqual(
            balancer.resolve_host("subdomain.local.ep.io").__class__,
            Spin,
        )
        self.assertEqual(
            balancer.resolve_host("subdomain.ep.io").__class__,
            Redirect,
        )
        self.assertEqual(
            balancer.resolve_host("multi.level.subdomain.local.ep.io").__class__,
            Spin,
        )
        # Test nonexistent base name
        self.assertEqual(
            balancer.resolve_host("i-love-bees.com").__class__,
            Unknown,
        )
