#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pandarus-remote web server.

Usage:
  pandarus-remote [--port=<port>] [--localhost]
  pandarus-remote -h | --help
  pandarus-remote --version

Options:
  --localhost   Only allow connections from this computer.
  -h --help     Show this screen.
  --version     Show version.

"""
from docopt import docopt
from pandarus_remote import pr_app
import os


def webapp():
    args = docopt(__doc__, version='Pandarus-remote web service 1.0')
    port = int(args.get("--port", False) or 5000)
    host = "localhost" if args.get("--localhost", False) else "0.0.0.0"

    print("pandarus-remote started on {}:{}".format(host, port))

    pr_app.run(host=host, port=port, debug=False)
