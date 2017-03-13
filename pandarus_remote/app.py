# -*- coding: utf-8 -*-
from . import pr_app
from .db import (
    database,
    File,
    Intersection,
)
from .filesystem import data_dir
from .utils import sha256, is_valid_spatial_dataset
from flask import (
    abort,
    request,
    Response,
    send_file,
    url_for,
)
from peewee import DoesNotExist
from werkzeug import secure_filename
import hashlib
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
        'files': [(obj.name, obj.sha256) for obj in File.select()],
        'intersections': [
            (obj.first.sha256, obj.second.sha256)
            for obj in Intersection.select()
        ],
        'remaining': [
            (vector.sha256, raster.sha256)
            for obj in RasterStats.select()
        ],
        'rasterstats': [
            (vector.sha256, raster.sha256)
            for obj in RasterStats.select()
        ],
    })


def get_intersection(vector=False):
    first = request.form['first']
    second = request.form['second']

    # Make sure the hashes aren't the same
    if first == second:
        abort(406, "Identical file hashes")

    # Make sure Files exist
    try:
        first = File.get(File.sha256 == first)
    except:
        abort(404, "Can't find first file in database")
    try:
        second = File.get(File.sha256 == second)
    except:
        abort(404, "Can't find second file in database")

    try:
        obj = Intersection.get(
            Intersection.first == first & \
            Intersection.second == second
        )
    except:
        abort(404, "Can't find intersection")

    if vector:
        fp = obj.vector_fp
    else:
        fp = obj.data_fp

    return send_file(
        fp,
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=os.path.basename(fp)
    )


@pr_app.route('/intersection/vector', methods=['POST'])
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
    kind = request.form['kind']
    new_name = uuid.uuid4().hex + "." + filename
    filepath = os.path.join(
        data_dir,
        "uploads",
        new_name
    )

    if kind == 'vector':
        layer, band, field = request.form['layer'] or None, None, request.form['field']
    elif kind == 'raster':
        layer, band, field = None, request.form['band'] or None, None
    else:
        # Invalid `kind` field
        abort(406, "Invalid 'kind' value")

    # File can't exist
    if os.path.isfile(filepath):
        abort(409, "This file already exists")
    file_obj.save(filepath)
    our_hash = sha256(filepath)

    # Provided hash is incorrect
    if our_hash != their_hash:
        os.remove(filepath)
        abort(406, "Can't reproduce provided hash value")

    # Make sure valid spatial dataset
    if not is_valid_spatial_dataset(filepath):
        os.remove(filepath)
        abort(406, "Not a valid vector or raster file")

    # Hash already exists
    if File.select().where(File.sha256 == our_hash).count():
        os.remove(filepath)
        abort(409, "This file hash is already uploaded")

    File(filepath=filepath, name=new_name, sha256=our_hash, kind=kind,
         layer=layer, band=band, field=field).save()

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

    # Make sure the hashes aren't the same
    if first_h == second_h:
        abort(406, "Identical file hashes")

    # Make sure Files exist
    try:
        first = File.get(File.sha256 == first_h)
    except:
        abort(404, "Can't find first file in database")
    try:
        second = File.get(File.sha256 == second_h)
    except:
        abort(404, "Can't find second file in database")

    # Make sure correct types

    # Make sure Intersection doesn't exist
    if Intersection.select().where(
            Intersection.first == first & \
            Intersection.second == second).count():
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

    # Make sure the hashes aren't the same
    if first_h == second_h:
        abort(406, "Identical file hashes")

    # Make sure Files exist
    try:
        first = File.get(File.sha256 == first_h)
    except:
        abort(404, "Can't find first file in database")
    try:
        second = File.get(File.sha256 == second_h)
    except:
        abort(404, "Can't find second file in database")

    if first.kind != 'vector' or second.kind != 'vector':
        abort(406, "Not vector file(s)")

    try:
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
