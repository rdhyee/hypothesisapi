#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='hypothesisapi',
    version='0.2.0',
    description="Python wrapper for the hypothes.is web API",
    long_description=readme + '\n\n' + history,
    author="Raymond Yee",
    author_email='raymond.yee@gmail.com',
    url='https://github.com/rdhyee/hypothesisapi',
    packages=[
        'hypothesisapi',
    ],
    package_dir={'hypothesisapi':
                 'hypothesisapi'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='hypothesisapi',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
