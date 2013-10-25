#!/usr/bin/env python
from setuptools import setup

setup(
    name='cos_syncer',
    version='1.0.0',
    description="A script that syncs a local file system to the COS",
    long_description=open('README.md').read(),
    author='HubSpot Dev Team',
    author_email='devteam+hapi@hubspot.com',
    url='https://github.com/HubSpot/cos_syncer',
    download_url='https://github.com/HubSpot/cos_syncer/tarball/v1.0.0',
    license='LICENSE.txt',
    packages=['cos_syncer'],
    install_requires=[
        'nose==1.1.2',
        'unittest2==0.5.1',
        'simplejson>=2.1.2',
        'hapipy>=2.10.4'
    ],
)
