#!/usr/bin/env python
# Note: to use the 'upload' functionality of this file, you must:
# $ pip install twine

from setuptools import setup
import versioneer

setup(
    version=versioneer.get_version(),
    install_requires=[
        'asciimatics>=1.11.0',
        'PyYAML>=5.3',
        'requests>=2.22.0',
        'ConfigArgParse>-1.0'
    ],
    extras_require={
        'testing': ["mock", "tox"]
    },
    cmdclass=versioneer.get_cmdclass(),
)
