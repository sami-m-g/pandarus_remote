# -*- coding: utf-8 -*-
from .db import Intersection, File
from pandarus import Pandarus
import os


def intersect(fp1, hash1, meta1, fp2, hash2, meta2, output_fp):
    try:
        cpus = int(os.environ['PANDARUS_CPUS'])
        assert cpus
    except:
        cpus = None

    pan = Pandarus(
        from_filepath=fp1,
        from_metadata=meta1,
        to_filepath=fp2,
        to_metadata=meta2,
    )
    pan.match(cpus=cpus)
    pan.add_to_map_fieldname()
    pan.add_from_map_fieldname()
    output_fp = pan.export(output_fp)

    first = File.get(File.sha256 == hash1)
    second = File.get(File.sha256 == hash2)

    # Job enqueued twice
    if Intersection.select().where(
            Intersection.first << (first, second) & \
            Intersection.second << (second, first)).count():
        return

    Intersection(
        first=first,
        second=second,
        output_fp=output_fp
    ).save()
