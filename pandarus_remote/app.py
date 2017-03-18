# -*- coding: utf-8 -*-
from . import pr_app
from .db import (
    database,
    File,
    Intersection,
    RasterStats,
    Remaining,
)
from .filesystem import data_dir
from .utils import sha256, check_type
from flask import (
    abort,
    request,
    Response,
    send_file,
    url_for,
)
from peewee import DoesNotExist
from werkzeug import secure_filename
import fiona
import json
import os
import uuid
from .tasks import (
    intersect_task,
    rasterstats_task,
    remaining_task,
)
from . import redis_queue
from . import __version__ as version


def json_response(data):
    return Response(json.dumps(data), mimetype='application/json')


@pr_app.route('/')
def ping():
    return """pandarus_remote web service, version {}.""".format(version)


@pr_app.route("/status/<job_id>")
def status(job_id):
    try:
        job = redis_queue.fetch_job(job_id)
    except:
        abort(404)
    if not job:
        abort(404)
    return job.status


@pr_app.route('/catalog')
def catalog():
    return json_response({
        'files': [(obj.name, obj.sha256, obj.kind) for obj in File.select()],
        'intersections': [
            (obj.first.sha256, obj.second.sha256)
            for obj in Intersection.select()
        ],
        'remaining': [
            (obj.intersection.first.sha256, obj.intersection.second.sha256)
            for obj in Remaining.select()
        ],
        'rasterstats': [
            (obj.vector.sha256, obj.raster.sha256)
            for obj in RasterStats.select()
        ],
    })


@pr_app.route('/rasterstats', methods=['POST'])
def get_rasterstats():
    vector = request.form['vector']
    raster = request.form['raster']

    try:
        vector = File.get(File.sha256 == vector)
        raster = File.get(File.sha256 == raster)
        rs = RasterStats.get(
            (RasterStats.vector == vector) &
            (RasterStats.raster == raster)
        )
    except DoesNotExist:
        abort(404, "Can't find raster stats result")

    return send_file(
        rs.output,
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=os.path.basename(rs.output)
    )


@pr_app.route('/remaining', methods=['POST'])
def get_remaining():
    first = request.form['first']
    second = request.form['second']

    try:
        first = File.get(File.sha256 == first)
        second = File.get(File.sha256 == second)
        intersection = Intersection.get(
            (Intersection.first == first) &
            (Intersection.second == second)
        )
        remaining = Remaining.get(
            Remaining.intersection == intersection
        )
    except DoesNotExist:
        abort(404, "Can't find remaining result")

    return send_file(
        remaining.data_fp,
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=os.path.basename(remaining.data_fp)
    )


def _get_intersection(vector=False):
    first = request.form['first']
    second = request.form['second']

    try:
        first = File.get(File.sha256 == first)
        second = File.get(File.sha256 == second)
        obj = Intersection.get(
            (Intersection.first == first) &
            (Intersection.second == second)
        )
    except:
        abort(404, "Can't find intersection")

    fp = obj.vector_fp if vector else obj.data_fp

    return send_file(
        fp,
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=os.path.basename(fp)
    )


@pr_app.route('/intersection-file', methods=['POST'])
def get_vector_intersection():
    return _get_intersection(vector=True)


@pr_app.route('/intersection', methods=['POST'])
def get_vector():
    return _get_intersection()


@pr_app.route('/upload', methods=['POST'])
def upload():
    their_hash = request.form['sha256']
    filename = secure_filename(request.form['name'])
    file_obj = request.files['file']
    new_name = uuid.uuid4().hex + "." + filename
    filepath = os.path.join(
        data_dir,
        "uploads",
        new_name
    )

    file_obj.save(filepath)

    our_hash = sha256(filepath)
    kind = check_type(filepath)

    if kind == 'vector':
        layer, band, field = request.form['layer'] or None, None, request.form['field']
        with fiona.open(filepath) as src:
            geom_type = src.meta['schema']['geometry']
    elif kind == 'raster':
        layer, band, field, geom_type = None, request.form['band'] or None, None, None
    else:
        os.remove(filepath)
        abort(406, "Invalid spatial dataset")

    # Provided hash is incorrect
    if our_hash != their_hash:
        os.remove(filepath)
        abort(406, "Can't reproduce provided hash value")

    # Hash already exists
    if File.select().where(File.sha256 == our_hash).count():
        os.remove(filepath)
        abort(409, "This file hash is already uploaded")

    File(
        band=band,
        field=field,
        filepath=filepath,
        geometry_type=geom_type,
        kind=kind,
        layer=layer,
        name=new_name,
        sha256=our_hash,
    ).save()

    return json_response(
        {
            'filename': new_name,
            'sha256': our_hash
        }
    )


@pr_app.route('/calculate-intersection', methods=['POST'])
def calculate_intersection():
    first_h = request.form['first']
    second_h = request.form['second']

    try:
        first = File.get(File.sha256 == first_h)
        second = File.get(File.sha256 == second_h)
    except DoesNotExist:
        abort(404, "File not found")

    # Make sure the hashes aren't the same
    if first_h == second_h:
        abort(406, "Identical file hashes")

    # Correct file types
    if not first.kind == 'vector' and second.kind == 'vector':
        abort(406, "Both files must be vector datasets")

    # Make sure correct types
    if not second.geometry_type in ("Polygon", "MultiPolygon"):
        abort(406, "Invalid geometry type for intersection")

    # Make sure Intersection doesn't exist
    if Intersection.select().where(
            (Intersection.first == first) &
            (Intersection.second == second)).count():
        abort(409, "This intersection already exists")

    job = redis_queue.enqueue(
        intersect_task,
        first.id,
        second.id,
        os.path.join(data_dir, "intersections"),
        timeout=60 * 60 * 4
    )

    return url_for("status", job_id=job.id)


@pr_app.route('/calculate-remaining', methods=['POST'])
def calculate_remaining():
    first_h = request.form['first']
    second_h = request.form['second']

    try:
        first = File.get(File.sha256 == first_h)
        second = File.get(File.sha256 == second_h)
        intersection = Intersection.get(
            Intersection.first == first,
            Intersection.second == second
        )
    except DoesNotExist:
        abort(404, "Intersection not calculated")

    # Make sure Remaining doesn't exist
    if Remaining.select().where(Remaining.intersection == intersection).count():
        abort(409, "This remaining calculation result already exists")

    job = redis_queue.enqueue(
        remaining_task,
        intersection.id,
        os.path.join(data_dir, "remaining"),
        timeout=60 * 30
    )

    return url_for("status", job_id=job.id)


@pr_app.route('/calculate-rasterstats', methods=['POST'])
def calculate_rasterstats():
    vector_h = request.form['vector']
    raster_h = request.form['raster']

    try:
        vector = File.get(File.sha256 == vector_h)
        raster = File.get(File.sha256 == raster_h)
    except DoesNotExist:
        abort(404, "File not found")

    if not vector.kind == 'vector' and raster.kind == 'raster':
        abort(406, "Invalid data file types")

    # Make sure doesn't already exist
    if RasterStats.select().where(
        (RasterStats.vector == vector) &
        (RasterStats.raster == raster)
    ).count():
        abort(409, "This raster calculation result already exists")

    output = os.path.join(data_dir, "rasterstats", uuid.uuid4().hex + '.json')

    job = redis_queue.enqueue(
        rasterstats_task,
        vector.id,
        raster.id,
        raster.band,
        output,
        timeout=60 * 30
    )

    return url_for("status", job_id=job.id)
