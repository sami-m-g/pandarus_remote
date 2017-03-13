# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    author="Chris Mutel",
    author_email="cmutel@gmail.com",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
    entry_points = {
        'console_scripts': [
            'pandarus-remote = pandarus_remote.bin:webapp',
        ]
    },
    install_requires=[
        "appdirs",
        "docopt",
        "fiona",
        "flask",
        "numpy",
        "pandarus",
        "peewee",
        "rasterio",
        "requests",
        "rq",
    ],
    license=open('LICENSE.txt').read(),
    long_description=open('README.rst').read(),
    name='pandarus_remote',
    packages=["pandarus_remote"],
    url="https://bitbucket.org/cmutel/pandarus_remote",
    version="0.2",
)
