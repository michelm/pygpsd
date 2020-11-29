#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Michel Mooij, michel.mooij7@gmail.com

import os, importlib, importlib.util, inspect
from setuptools import setup

url = 'https://github.com/michelm/pygpsd'

with open('README.md') as f:
    long_description = f.read()

def get_version() -> str:
    fname = os.path.join(os.path.dirname(__file__), 'pygpsd', '__init__.py')
    spec = importlib.util.spec_from_file_location('__init__', fname)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    members = inspect.getmembers(module)
    ver = [v for v in members if v[0] == 'version']
    return ver[0][1]

version = get_version()

setup(
    name = 'pygpsd',
    version = version,
    author = 'Michel Mooij',
    author_email = 'michel.mooij7@gmail.com',
    maintainer = 'Michel Mooij',
    maintainer_email = 'michel.mooij7@gmail.com',
    url = url,
    download_url = "%s/downloads/pygpsd-%s.tar.gz" % (url, version),
    description = 'Simulated GPS daemon',
    long_description = long_description,
    packages = ['pygpsd'],
    package_data = {
        'pygpsd': [
            'data/*'
        ]
    },
    include_package_data=True,
    install_requires = [
        'distro',
        'wheel',
        'pynmea2'
    ],
    license = 'MIT',
    keywords = ['gps', 'gpsd', 'nmea'],
    platforms = 'any',
    entry_points = {
        'console_scripts': [
            ['pygpsd = pygpsd.main:main']
        ],
    },
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities"
    ]
)

