#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Legacy setup.py for backward compatibility.

Note: This project now uses pyproject.toml for configuration.
This file is maintained for editable installs with older pip versions.
"""

from setuptools import setup

# The actual configuration is in pyproject.toml
# This minimal setup.py allows `pip install -e .` to work with older pip
setup()
