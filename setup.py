#!/usr/bin/python
# -*- coding: utf-8 -*-

''' distutils/setuptools install script. '''

import os

from setuptools import setup, find_packages

here = os.path.dirname(__file__)

setup(
    name='setsts',
    version='1.0.0',
    install_requires=[
        'awscli', 'boto3'
    ],
    packages=find_packages(exclude=['tests', 'tests.*', 'docs']),
    entry_points={
        'console_scripts': [
            'setsts = setsts.setsts:main',
        ]
    }
)
