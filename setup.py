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
    author = "Epio Limited",
    author_email= "team@ep.io",
    description = 'A pure-Python loadbalancer.',
    packages = find_packages("."),
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
    ],
    entry_points = """
        [console_scripts]
        mantrid = mantrid.loadbalancer:Balancer.main
        mantrid-client = mantrid.cli:MantridCli.main
    """,
    package_data = {
        "mantrid": ["errors/*.http"],
    },
    requires = [
        "argparse",
        "eventlet (>=0.9.16)",
    ],
)
