#!/usr/bin/env python3

import os
import re
import sys
from distutils.core import setup

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise RuntimeError("Only Python 3.6 and greater is supported.")

with open(os.path.join(os.path.dirname(__file__), 'README.rst'), 'r') as f:
    readme = f.read()

VERSION = '0.7.0'


def verify_version(version: str) -> str:
    """
    If uploading, ensure the environment is Travis CI and that a tag is being
    deployed which matches the project's version (shown above)
    """
    # ensure travis ci
    if not 'upload' in sys.argv:
        return version

    if os.getenv('TRAVIS') != 'true':
        raise Exception("Upload can only be done within travis ci")

    # ensure tag matches version
    tag = os.getenv('TRAVIS_TAG')
    if not re.match('^v{version}$'.format(version=version), tag):
        raise Exception(f"Tag {tag} does not match project's version v{version}")

    return version


if __name__ == '__main__':
    setup(
        name='typycal',
        description='Easily add type intelligence to simple Python objects',
        long_description=readme,
        version=verify_version(VERSION),
        packages=['typycal'],
        url='https://github.com/cardinal-health/typycal',
        author='Cardinal Health',
        author_email='jackson.gilman@cardinalhealth.com',
        maintainer='Jackson J. Gilman',
        maintainer_email='jackson.gilman@cardinalhealth.com',
        license='Apache License 2.0',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Topic :: Software Development :: Libraries',
            'Topic :: Software Development :: Quality Assurance'
        ],
    )
