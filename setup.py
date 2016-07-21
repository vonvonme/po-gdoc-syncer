#!/usr/bin/env python

from setuptools import setup

setup(
    name='po-gdoc-syncer',
    version='1.0.0',
    description='PO file synchronizer for Google Docs',
    author='Beren Song',
    author_email='beren.song@vonvon.me',
    url='https://github.com/vonvonme/po-gdoc-syncer.git',
    packages=['posyncer'],
    entry_points={
        'console_scripts': [
            'sync-po-gdoc = posyncer.cmd:main'
        ]
    },
    install_requires=[
        'polib==1.0.7',
        'gspread==0.4.1',
        'oauth2client==2.2.0'
    ]
)
