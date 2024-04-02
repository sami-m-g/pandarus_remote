#!/bin/bash

gunicorn -w 1 -b 0.0.0.0:5000 "pandarus_remote.app:create_app()" --log-level=debug
