# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    author="Chris Mutel",
    author_email="cmutel@gmail.com",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
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
        "pandarus>=1.0",
        "peewee",
        "rasterio",
        "redis",
        "requests",
        "rq",
    ],
    license=open('LICENSE.txt').read(),
    long_description=open('README.rst').read(),
    name='pandarus_remote',
    packages=["pandarus_remote"],
    url="https://github.com/cmutel/pandarus_remote",
    version="1.0",
)
