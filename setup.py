#!/usr/bin/python

# Use setuptools if we can
try:
    from setuptools import setup
except ImportError:
    from distutils import setup

from mantrid import __version__

setup(
    name = 'mantrid',
    version = __version__,
    author = "Epio Limited",
    author_email= "team@ep.io",
    url = "http://github.com/epio/mantrid/",
    description = 'A pure-Python loadbalancer.',
    packages = [
        "mantrid",
        "mantrid.tests",
    ],
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
        "mantrid": ["static/*.http"],
    },
    install_requires = [
        "httplib2",
        "argparse",
        "eventlet>=0.9.16",
    ],
)
