# -*- coding: utf-8 -*-
__all__ = ['pr_app']

__version__ = (1, 0)

from flask import Flask
from redis import Redis
from rq import Queue

redis_queue = Queue(connection=Redis())
pr_app = Flask("PRemote")

# Default limit for file uploads is 250 MB
pr_app.config['MAX_CONTENT_LENGTH'] = 250 * 1024 * 1024

from . import app
