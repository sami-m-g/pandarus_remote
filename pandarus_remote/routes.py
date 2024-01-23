"""Routes for the __pandarus_remote__ web service."""
import os
from http import HTTPStatus
from pathlib import Path
from typing import Tuple

from flask import Blueprint, Response, request, send_file, url_for

from .errors import (
    FileAlreadyExistsError,
    IntersectionWithSelfError,
    InvalidIntersectionFileTypesError,
    InvalidIntersectionGeometryTypeError,
    InvalidRasterstatsFileTypesError,
    InvalidSpatialDatasetError,
    JobNotFoundError,
    NoneReproducibleHashError,
    QueryError,
    ResultAlreadyExistsError,
)
from .helpers import DatabaseHelper, IOHelper, RedisHelper
from .version import __version__

routes_blueprint = Blueprint("bp", __name__)


@routes_blueprint.route("/")
def ping() -> Tuple[Response, int]:
    """Ping the web service and return current version running."""
    return {"message": f"pandarus_remote web service {__version__}."}, HTTPStatus.OK


@routes_blueprint.route("/catalog")
def catalog() -> Tuple[Response, int]:
    """Get a catalog of spatial datasets and results currently available on the
    server."""
    return (DatabaseHelper().catalog, HTTPStatus.OK)


@routes_blueprint.route("/status/<job_id>")
def status(job_id: str) -> Tuple[Response, int]:
    """Get the status of a currently running job. Job status URLs are
    returned by the ``/calculate_intersection`` and ``/calculate_area``
    endpoints."""
    try:
        return RedisHelper().get_job_status(job_id), HTTPStatus.OK
    except JobNotFoundError:
        return {"error": f"Job with id: {job_id} is not found."}, HTTPStatus.NOT_FOUND


@routes_blueprint.route("/raster_stats", methods=["POST"])
def get_raster_stats() -> Tuple[Response, int]:
    """Request the download of the JSON data file from a raster stats calculation.
    Both spatial datasets should already be on the server (see ``/upload``), and
    the raster stats should already be calculated (see ``/calculate_rasterstats``)."""
    try:
        result = (
            DatabaseHelper()
            .get_raster_stats(request.form["vector"], request.form["raster"])
            .ouput
        )
        return (
            send_file(
                result,
                mimetype="application/octet-stream",
                as_attachment=True,
                download_name=os.path.basename(result),
            ),
            HTTPStatus.OK,
        )
    except QueryError as e:
        return {"error": str(e)}, HTTPStatus.NOT_FOUND


@routes_blueprint.route("/intersection", methods=["POST"])
def get_intersection() -> Tuple[Response, int]:
    """Request the download of a pandarus intersections JSON data file
    for two spatial datasets. Both spatial datasets should already be on
    the server (see ``/upload``), and the intersection should already be
    calculated (see ``/calculate_intersection``)."""
    try:
        result = (
            DatabaseHelper()
            .get_intersection(request.form["first"], request.form["second"])
            .data_file_path
        )
        return (
            send_file(
                result,
                mimetype="application/octet-stream",
                as_attachment=True,
                download_name=os.path.basename(result),
            ),
            HTTPStatus.OK,
        )
    except QueryError as e:
        return {"error": str(e)}, HTTPStatus.NOT_FOUND


@routes_blueprint.route("/remaining", methods=["POST"])
def get_remaining() -> Tuple[Response, int]:
    """Request the download of the JSON data file from a remaining
    areas calculation. Both spatial datasets should already be on
    he server (see ``/upload``), and the remaining areas should
    already be calculated (see ``/calculate_remaining``)."""
    try:
        result = (
            DatabaseHelper()
            .get_remaining(request.form["first"], request.form["second"])
            .data_file_path
        )
        return (
            send_file(
                result,
                mimetype="application/octet-stream",
                as_attachment=True,
                download_name=os.path.basename(result),
            ),
            HTTPStatus.OK,
        )
    except QueryError as e:
        return {"error": str(e)}, HTTPStatus.NOT_FOUND


@routes_blueprint.route("/upload", methods=["POST"])
def upload() -> Tuple[Response, int]:
    """Upload a spatial data file. The provided file must be
    openable by `fiona <https://github.com/Toblerity/Fiona>`__
    or `rasterio <https://github.com/mapbox/rasterio>`__."""
    try:
        file = IOHelper().save_uploaded_file(
            file=request.files["file"],
            name=request.form["name"],
            file_hash=request.form["sha256"],
            layer=request.form["layer"],
            field=request.form["field"],
            band=request.form["band"],
        )
        DatabaseHelper().add_uploaded_file(file)
        return {"filen_name": file.name, "sha256": file.sha256}, HTTPStatus.OK
    except InvalidSpatialDatasetError as isde:
        return {"error": str(isde)}, HTTPStatus.UNPROCESSABLE_ENTITY
    except NoneReproducibleHashError as nrhe:
        return {"error": str(nrhe)}, HTTPStatus.BAD_REQUEST
    except FileAlreadyExistsError as fae:
        Path(file.file_path).unlink()
        return {"error": str(fae)}, HTTPStatus.CONFLICT


@routes_blueprint.route("/calculate_intersection", methods=["POST"])
def calculate_intersection() -> Tuple[Response, int]:
    """Calculate a pandarus intersections file for two vector spatial datasets.
    Both spatial datasets should already be on the server (see ``/upload``).
    The second vector dataset must have the geometry type ``Polygon`` or
    ``MultiPolygon``."""
    file1_hash = request.form["first"]
    file2_hash = request.form["second"]
    if file1_hash == file2_hash:
        return {
            "error": str(IntersectionWithSelfError(file1_hash))
        }, HTTPStatus.BAD_REQUEST

    try:
        file1, file2 = DatabaseHelper().get_intersection(
            file1_hash, file2_hash, should_exist=False
        )
        if not file1.kind == "vector" and file2.kind == "vector":
            exception = InvalidIntersectionFileTypesError(
                file1_hash, file1.kind, file2_hash, file2.kind
            )
            return {"error": str(exception)}, HTTPStatus.BAD_REQUEST
        if file2.geometry_type not in ("Polygon", "MultiPolygon"):
            exception = InvalidIntersectionGeometryTypeError(
                file1_hash, file1.kind, file2_hash, file2.kind
            )
            return {"error": str(exception)}, HTTPStatus.BAD_REQUEST
        job = RedisHelper().enqueue_intersect_job(file1, file2)
        return url_for("status", job_id=job.id), HTTPStatus.ACCEPTED
    except ResultAlreadyExistsError as raee:
        return {"error": str(raee)}, HTTPStatus.CONFLICT
    except FileNotFoundError as fnfe:
        return {"error": str(fnfe)}, HTTPStatus.NOT_FOUND


@routes_blueprint.route("/calculate_rasterstats", methods=["POST"])
def calculate_rasterstats() -> Tuple[Response, int]:
    """Calculate a raster stats file for a vector and a raster spatial dataset.
    Both spatial datasets should already be on the server (see ``/upload``)."""
    vector_hash = request.form["vector"]
    raster_hash = request.form["raster"]

    try:
        vector, raster = DatabaseHelper().get_raster_stats(
            vector_hash, raster_hash, should_exist=False
        )
        if not vector.kind == "vector" or not raster.kind == "raster":
            exception = InvalidRasterstatsFileTypesError(
                vector_hash, vector.kind, raster_hash, raster.kind
            )
            return {"error": str(exception)}, HTTPStatus.BAD_REQUEST
        job = RedisHelper().enqueue_raster_stats_job(vector, raster, raster.band)
        return url_for("status", job_id=job.id), HTTPStatus.ACCEPTED
    except ResultAlreadyExistsError as raee:
        return {"error": str(raee)}, HTTPStatus.CONFLICT
    except FileNotFoundError as fnfe:
        return {"error": str(fnfe)}, HTTPStatus.NOT_FOUND


@routes_blueprint.route("/calculate_remaining", methods=["POST"])
def calculate_remaining() -> Tuple[Response, int]:
    """Calculate a remaining areas file for two vector spatial datasets.
    Both spatial datasets should already be on the server (see ``/upload``)."""
    first_hash = request.form["first"]
    second_hash = request.form["second"]

    try:
        remaining = DatabaseHelper().get_remaining(
            first_hash, second_hash, should_exist=False
        )
        job = RedisHelper().enqueue_remaining_job(remaining.intersection.id)
        return url_for("status", job_id=job.id), HTTPStatus.ACCEPTED
    except ResultAlreadyExistsError as raee:
        return {"error": str(raee)}, HTTPStatus.CONFLICT
    except FileNotFoundError as fnfe:
        return {"error": str(fnfe)}, HTTPStatus.NOT_FOUND
