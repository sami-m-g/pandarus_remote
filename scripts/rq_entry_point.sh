#!/bin/bash

rq worker-pool -u redis://redis:6379 --logging-level info
