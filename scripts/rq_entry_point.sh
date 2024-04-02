#!/bin/bash

rq worker-pool -u redis://redis:6379/0 --logging-level info
