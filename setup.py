#!/usr/bin/python

# Use setuptools if we can
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils import setup, find_packages

from mantrid import __version__

setup(
    name = 'mantrid',
    version = __version__,
    description = 'A pure-Python loadbalancer.',
    packages = find_packages("."),
    entry_points = """
        [console_scripts]
        mantrid = mantrid.loadbalancer:Balancer.main
        mantrid-client = mantrid_client.cli:MantridCli.main
    """,
)
