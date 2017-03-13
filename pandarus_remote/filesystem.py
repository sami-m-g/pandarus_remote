# -*- coding: utf-8 -*-
import appdirs
import os


def create_dir(dirpath):
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)

data_dir = appdirs.user_data_dir("PandarusRemote", "PR")
# logs_dir = appdirs.user_log_dir("PandarusRemote", "PR")

create_dir(data_dir)
create_dir(os.path.join(data_dir, "uploads"))
create_dir(os.path.join(data_dir, "areas"))
create_dir(os.path.join(data_dir, "intersections"))
# create_dir(logs_dir)
