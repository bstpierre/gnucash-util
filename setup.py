#!/usr/bin/env python

import os
from setuptools import setup


PROJECT = u'gnucash-util'
VERSION = '0.1'
URL = 'https://github.com/bstpierre/gnucash-util'
AUTHOR = u'Brian St. Pierre'
AUTHOR_EMAIL = u'brian@bstpierre.org'
DESC = "A collection of utilities for automating GnuCash 2.4+."

def read_file(file_name):
    file_path = os.path.join(
        os.path.dirname(__file__),
        file_name
        )
    return open(file_path).read()

setup(
    name=PROJECT,
    version=VERSION,
    description=DESC,
    long_description=read_file('README.rst'),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license='MIT License',
    packages=['gnucash_util'],
    scripts=['scripts/gnc-freshbooks-import-invoice', ],
    include_package_data=True,
    install_requires=[
        # -*- Requirements -*-
        ## GnuCash-2.4
    ],
    entry_points = {
        # -*- Entry points -*-
    },
    classifiers=[
        # -*- Classifiers -*-
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Topic :: Office/Business :: Financial :: Accounting",
    ]
)
