#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='Django-Astro',
    version='0.1',
    description='Astronomy calculations',
    author='Mark Sundstrom',
    author_email='mark@mhsundstrom.com',

    packages=find_packages(),
    include_package_data=True,

    zip_safe=False,
)
