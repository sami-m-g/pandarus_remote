"""Routes for the __pandarus_remote__ web service."""

from http import HTTPStatus
from pathlib import Path

from flask import Blueprint, Response, request

from .errors import (
    FileAlreadyExistsError,
    IntersectionWithSelfError,
    InvalidIntersectionFileTypesError,
    InvalidIntersectionGeometryTypeError,
    InvalidRasterstatsFileTypesError,
    InvalidSpatialDatasetError,
    JobNotFoundError,
    NoneReproducibleHashError,
)
from .helpers import DatabaseHelper, IOHelper, RedisHelper
from .utils import calculate_endpoint, get_calculation_endpoint
from .version import __version__

routes_blueprint = Blueprint("routes_blueprint", __name__)


@routes_blueprint.route("/")
def ping() -> Response:
    """Ping the web service and return current version running."""
    return {"message": f"pandarus_remote web service {__version__}."}, HTTPStatus.OK


@routes_blueprint.route("/catalog")
def catalog() -> Response:
    """Get a catalog of spatial datasets and results currently available on the
    server."""
    return DatabaseHelper().catalog, HTTPStatus.OK


@routes_blueprint.route("/status/<job_id>")
def status(job_id: str) -> Response:
    """Get the status of a currently running job. Job status URLs are
    returned by the ``/calculate_intersection`` and ``/calculate_area``
    endpoints."""
    try:
        return RedisHelper().get_job_status(job_id), HTTPStatus.OK
    except JobNotFoundError as jnfe:
        return {"error": str(jnfe)}, HTTPStatus.NOT_FOUND


@routes_blueprint.route("/raster_stats", methods=["POST"])
@get_calculation_endpoint
def get_raster_stats() -> str:
    """Request the download of the JSON data file from a raster stats calculation.
    Both spatial datasets should already be on the server (see ``/upload``), and
    the raster stats should already be calculated (see ``/calculate_rasterstats``)."""
    return (
        DatabaseHelper()
        .get_raster_stats(request.form["vector"], request.form["raster"])
        .output_file_path
    )


@routes_blueprint.route("/intersection", methods=["POST"])
@get_calculation_endpoint
def get_intersection() -> str:
    """Request the download of a pandarus intersections JSON data file
    for two spatial datasets. Both spatial datasets should already be on
    the server (see ``/upload``), and the intersection should already be
    calculated (see ``/calculate_intersection``)."""
    return (
        DatabaseHelper()
        .get_intersection(request.form["first"], request.form["second"])
        .data_file_path
    )


@routes_blueprint.route("/remaining", methods=["POST"])
@get_calculation_endpoint
def get_remaining() -> str:
    """Request the download of the JSON data file from a remaining
    areas calculation. Both spatial datasets should already be on
    he server (see ``/upload``), and the remaining areas should
    already be calculated (see ``/calculate_remaining``)."""
    return (
        DatabaseHelper()
        .get_remaining(request.form["first"], request.form["second"])
        .data_file_path
    )


@routes_blueprint.route("/upload", methods=["POST"])
def upload() -> Response:
    """Upload a spatial data file. The provided file must be
    openable by `fiona <https://github.com/Toblerity/Fiona>`__
    or `rasterio <https://github.com/mapbox/rasterio>`__."""
    try:
        file = IOHelper().save_uploaded_file(
            file=request.files["file"],
            name=request.form["name"],
            file_hash=request.form["sha256"],
            layer=request.form.get("layer", None),
            field=request.form.get("field", None),
            band=request.form.get("band", 1),
        )
        DatabaseHelper().add_uploaded_file(file)
        return {"file_name": file.name, "file_sha256": file.sha256}, HTTPStatus.OK
    except InvalidSpatialDatasetError as isde:
        return {"error": str(isde)}, HTTPStatus.UNPROCESSABLE_ENTITY
    except NoneReproducibleHashError as nrhe:
        return {"error": str(nrhe)}, HTTPStatus.BAD_REQUEST
    except FileAlreadyExistsError as fae:
        Path(file.file_path).unlink()
        return {"error": str(fae)}, HTTPStatus.CONFLICT


@routes_blueprint.route("/calculate_intersection", methods=["POST"])
@calculate_endpoint
def calculate_intersection() -> str:
    """Calculate a pandarus intersections file for two vector spatial datasets.
    Both spatial datasets should already be on the server (see ``/upload``).
    The second vector dataset must have the geometry type ``Polygon`` or
    ``MultiPolygon``."""
    file1_hash = request.form["first"]
    file2_hash = request.form["second"]
    if file1_hash == file2_hash:
        raise IntersectionWithSelfError(file1_hash)

    file1, file2 = DatabaseHelper().get_intersection(
        file1_hash, file2_hash, should_exist=False
    )
    if file1.kind != "vector" or file2.kind != "vector":
        raise InvalidIntersectionFileTypesError(
            file1_hash, file1.kind, file2_hash, file2.kind
        )
    if file2.geometry_type not in ("Polygon", "MultiPolygon"):
        raise InvalidIntersectionGeometryTypeError(
            file1_hash, file1.kind, file2_hash, file2.kind
        )
    return RedisHelper().enqueue_intersection_job(file1, file2).id


@routes_blueprint.route("/calculate_raster_stats", methods=["POST"])
@calculate_endpoint
def calculate_rasterstats() -> str:
    """Calculate a raster stats file for a vector and a raster spatial dataset.
    Both spatial datasets should already be on the server (see ``/upload``)."""
    vector_hash = request.form["vector"]
    raster_hash = request.form["raster"]

    vector, raster = DatabaseHelper().get_raster_stats(
        vector_hash, raster_hash, should_exist=False
    )
    if vector.kind != "vector" or raster.kind != "raster":
        raise InvalidRasterstatsFileTypesError(
            vector.sha256, vector.kind, raster.sha256, raster.kind
        )
    return RedisHelper().enqueue_raster_stats_job(vector, raster, raster.band).id


@routes_blueprint.route("/calculate_remaining", methods=["POST"])
@calculate_endpoint
def calculate_remaining() -> str:
    """Calculate a remaining areas file for two vector spatial datasets.
    Both spatial datasets should already be on the server (see ``/upload``)."""
    first_hash = request.form["first"]
    second_hash = request.form["second"]
    intersection_id = DatabaseHelper().get_remaining(
        first_hash, second_hash, should_exist=False
    )
    return RedisHelper().enqueue_remaining_job(intersection_id).id
