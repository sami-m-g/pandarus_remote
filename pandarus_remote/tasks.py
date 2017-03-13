# -*- coding: utf-8 -*-
from .db import Intersection, File, RasterStats, Remaining
from pandarus import (
    intersect,
    raster_statistics,
    calculate_remaining,
)
import os


def intersect_task(id1, id2, output):
    try:
        cpus = int(os.environ['PANDARUS_CPUS'])
        assert cpus
    except:
        cpus = None

    first = File.get(File.id == id1)
    second = File.get(File.id == id2)

    # Job enqueued twice
    if Intersection.select().where(
            Intersection.first == first & \
            Intersection.second == second).count():
        return

    vector, data = intersect(
        first.filepath,
        first.field,
        second.filepath,
        second.field,
        dirpath = output,
        cpus=cpus,
        driver='GPKG'
    )

    if Intersection.select().where(
            Intersection.first == first & \
            Intersection.second == second).count():
        return

    Intersection(
        first=first,
        second=second,
        data_fp=data,
        vector_fp=vector,
    ).save()


def rasterstats_task(vector_id, raster_id, band, output_fp):
    vector = File.get(File.id == vector_id)
    raster = File.get(File.id == raster_id)

    # Job enqueued twice
    if RasterStats.select().where(
            RasterStats.vector == vector & \
            RasterStats.raster == raster).count():
        return

    raster_statistics(vector.filepath, vector.field, raster.filepath, output=output_fp, band=band)

    # Job enqueued twice
    if RasterStats.select().where(
            RasterStats.vector == vector & \
            RasterStats.raster == raster).count():
        return

    RasterStats(
        vector=vector,
        raster=raster,
        output=output_fp
    ).save()


def remaining_task(intersection_id, output):
    intersection = Intersection.get(Intersection.id == intersection_id)
    source = intersection.first

    # Job enqueued twice
    if Remaining.select().where(Remaining.intersection == intersection).count():
        return

    data_fp = calculate_remaining(
        source.filepath,
        source.field,
        intersection.vector_fp,
        dirpath=output
    )

    if Remaining.select().where(Remaining.intersection == intersection).count():
        return

    Remaining(
        intersection=intersection,
        data_fp=data_fp
    ).save()
