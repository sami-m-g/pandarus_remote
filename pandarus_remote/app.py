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
from werkzeug import secure_filename
import hashlib
import json
import os
import uuid
from .tasks import intersect, area
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
            (obj.first.name, obj.second.name, os.path.basename(obj.output_fp))
            for obj in Intersection.select()
        ],
        'areas': [
            (obj.reference.name, os.path.basename(obj.output_fp))
            for obj in Area.select()
        ],
    })


@pr_app.route('/intersection', methods=['POST'])
def get_intersection():
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
            Intersection.first << (first, second) & \
            Intersection.second << (first, second)
        )
    except:
        abort(404, "Can't find intersection")

    return send_file(
        obj.output_fp,
        mimetype='application/octet-stream',
        as_attachment=True,
        attachment_filename=os.path.basename(obj.output_fp)
    )


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

    # Make sure Intersection doesn't exist
    if Intersection.select().where(
            Intersection.first << (first, second) & \
            Intersection.second << (second, first)).count():
        abort(409, "This intersection already exists")

    def get_meta(obj):
        if obj.kind == 'vector':
            return {'layer': obj.layer, 'field': obj.field}
        else:
            return {'band': obj.band}

    output_filename = uuid.uuid4().hex
    output_fp = os.path.join(data_dir, "intersections", output_filename)
    job = redis_queue.enqueue(
        intersect,
        first.filepath,
        first_h,
        get_meta(first),
        second.filepath,
        second_h,
        get_meta(second),
        output_fp,
        timeout=60 * 60 * 4
    )

    return url_for("status", job_id=job.id)
