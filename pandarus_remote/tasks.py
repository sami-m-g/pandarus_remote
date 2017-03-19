# -*- coding: utf-8 -*-
from .db import Intersection, File, RasterStats, Remaining
from .filesystem import logs_dir
from .utils import sha256
from pandarus import (
    intersect,
    intersections_from_intersection,
    raster_statistics,
    calculate_remaining,
)
import fiona
import os


EXPORT_FORMAT = os.environ.get("PANDARUS_EXPORT_FORMAT") or 'GeoJSON'


def intersect_task(id1, id2, output):
    try:
        cpus = int(os.environ['PANDARUS_CPUS'])
        assert cpus
    except:
        cpus = None

    first = File.get(File.id == id1)
    second = File.get(File.id == id2)

    print("Intersect task:", first.name, second.name)

    # Job enqueued twice
    if Intersection.select().where(
            (Intersection.first == first) &
            (Intersection.second == second)).count():
        return

    vector, data = intersect(
        first.filepath,
        first.field,
        second.filepath,
        second.field,
        dirpath=output,
        cpus=cpus,
        driver=EXPORT_FORMAT,
        log_dir=logs_dir
    )

    if Intersection.select().where(
            (Intersection.first == first) &
            (Intersection.second == second)).count():
        return

    Intersection(
        first=first,
        second=second,
        data_fp=data,
        vector_fp=vector,
    ).save()

    # Save intersection data files for new spatial scale
    with fiona.open(vector) as src:
        geom_type = src.meta['schema']['geometry']

    third = File.create(
        filepath=vector,
        name=os.path.basename(vector),
        sha256=sha256(vector),
        band=None,
        layer=None,
        field='id',
        kind='vector',
        geometry_type=geom_type,
    )

    fp1, fp2 = intersections_from_intersection(
        vector,
        data,
        output
    )

    Intersection(
        first=third,
        second=first,
        data_fp=fp1,
        vector_fp=vector
    ).save()

    Intersection(
        first=third,
        second=second,
        data_fp=fp2,
        vector_fp=vector
    ).save()


def rasterstats_task(vector_id, raster_id, band, output_fp):
    vector = File.get(File.id == vector_id)
    raster = File.get(File.id == raster_id)

    # Job enqueued twice
    if RasterStats.select().where(
            (RasterStats.vector == vector) &
            (RasterStats.raster == raster)).count():
        return

    output = raster_statistics(vector.filepath, vector.field, raster.filepath, output=output_fp, band=band)

    # Job enqueued twice
    if RasterStats.select().where(
            (RasterStats.vector == vector) &
            (RasterStats.raster == raster)).count():
        return

    RasterStats(
        vector=vector,
        raster=raster,
        output=output
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
