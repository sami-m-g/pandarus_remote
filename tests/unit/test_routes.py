"""Test cases for the __routes__ module."""
from http import HTTPStatus
from typing import Any, Dict

from pandarus_remote import __version__
from pandarus_remote.errors import (
    FileAlreadyExistsError,
    IntersectionWithSelfError,
    InvalidIntersectionFileTypesError,
    InvalidIntersectionGeometryTypeError,
    InvalidRasterstatsFileTypesError,
    InvalidSpatialDatasetError,
    JobNotFoundError,
    NoneReproducibleHashError,
)
from pandarus_remote.helpers import DatabaseHelper, IOHelper, RedisHelper
from pandarus_remote.models import File, Intersection, RasterStats, Remaining

from .. import FILE_TEXT


class _MockJob:  # pylint: disable=too-few-public-methods
    """Mock the Job class."""

    def __init__(self, job_id: str) -> None:
        """Initialize the class."""
        self.id = job_id


def test_index(client) -> None:
    """Test that the index page is called correctly."""
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.json == {"message": f"pandarus_remote web service {__version__}."}


def test_catalog(client, monkeypatch) -> None:
    """Test that the catalog page is called correctly."""
    catalog = {
        "files": [],
        "intersections": [],
        "remainings": [],
        "raster_stats": [],
    }
    monkeypatch.setattr(DatabaseHelper, "catalog", catalog)

    response = client.get("/catalog")
    assert response.status_code == HTTPStatus.OK
    assert response.json == catalog


def test_status(client, monkeypatch) -> None:
    """Test that the status page is called correctly."""
    status = {"status": "queued", "result": None}

    def _mock_get_job_status(_: RedisHelper, __: str) -> Dict[str, Any]:
        return status

    monkeypatch.setattr(RedisHelper, "get_job_status", _mock_get_job_status)

    response = client.get("/status/job_id")
    assert response.status_code == HTTPStatus.OK
    assert response.json == status


def test_status_job_not_found(client, monkeypatch) -> None:
    """Test that the status page is called correctly with JobNotFoundError."""
    job_id = "job_id"
    error = JobNotFoundError(job_id)

    def _mock_get_job_status(_: RedisHelper, __: str) -> Dict[str, Any]:
        raise error

    monkeypatch.setattr(RedisHelper, "get_job_status", _mock_get_job_status)

    response = client.get(f"/status/{job_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json == {"error": str(error)}


def test_get_raster_stats(client, monkeypatch) -> None:
    """Test that the get_raster_stats endpoint is called correctly."""
    monkeypatch.setattr(
        DatabaseHelper,
        "get_raster_stats",
        lambda *_, **__: RasterStats(output_file_path=FILE_TEXT),
    )

    response = client.post(
        "/raster_stats", data={"vector": "vector", "raster": "raster"}
    )
    assert response.status_code == HTTPStatus.OK


def test_get_intersection(client, monkeypatch) -> None:
    """Test that the get_intersection endpoint is called correctly."""
    monkeypatch.setattr(
        DatabaseHelper,
        "get_intersection",
        lambda *_, **__: Intersection(data_file_path=FILE_TEXT),
    )

    response = client.post("/intersection", data={"first": "first", "second": "second"})
    assert response.status_code == HTTPStatus.OK


def test_get_remaining(client, monkeypatch) -> None:
    """Test that the get_remaining endpoint is called correctly."""
    monkeypatch.setattr(
        DatabaseHelper,
        "get_remaining",
        lambda *_, **__: Remaining(data_file_path=FILE_TEXT),
    )

    response = client.post("/remaining", data={"first": "first", "second": "second"})
    assert response.status_code == HTTPStatus.OK


def test_upload(client, monkeypatch, mock_uploaded_file) -> None:
    """Test that the upload endpoint is called correctly."""
    file, file_content = mock_uploaded_file
    monkeypatch.setattr(IOHelper, "save_uploaded_file", lambda *_, **__: file)
    monkeypatch.setattr(DatabaseHelper, "add_uploaded_file", lambda *_, **__: None)

    response = client.post(
        "/upload",
        data={
            "file": file_content,
            "name": "name",
            "sha256": "sha256",
            "layer": "layer",
            "field": "field",
            "band": "band",
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json == {"file_name": file.name, "file_sha256": file.sha256}


def test_upload_invalid_spatial_dataset(
    client, monkeypatch, mock_uploaded_file
) -> None:
    """Test that the upload endpoint is called correctly with
    InvalidSpatialDatasetError."""
    file_model, file_content = mock_uploaded_file
    error = InvalidSpatialDatasetError(file_model.name)

    def _mock_save_uploaded_file(*_, **__):
        raise error

    monkeypatch.setattr(IOHelper, "save_uploaded_file", _mock_save_uploaded_file)
    monkeypatch.setattr(DatabaseHelper, "add_uploaded_file", lambda *_, **__: None)

    response = client.post(
        "/upload",
        data={
            "file": file_content,
            "name": "name",
            "sha256": "sha256",
            "layer": "layer",
            "field": "field",
            "band": "band",
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json == {"error": str(error)}


def test_upload_non_reproducible_hash(client, monkeypatch, mock_uploaded_file) -> None:
    """Test that the upload endpoint is called correctly with
    NoneReproducibleHashError."""
    file_model, file_content = mock_uploaded_file
    error = NoneReproducibleHashError(file_model.name)

    def _mock_save_uploaded_file(*_, **__):
        raise error

    monkeypatch.setattr(IOHelper, "save_uploaded_file", _mock_save_uploaded_file)
    monkeypatch.setattr(DatabaseHelper, "add_uploaded_file", lambda *_, **__: None)

    response = client.post(
        "/upload",
        data={
            "file": file_content,
            "name": "name",
            "sha256": "sha256",
            "layer": "layer",
            "field": "field",
            "band": "band",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json == {"error": str(error)}


def test_upload_file_already_exists(
    tmp_path, client, monkeypatch, mock_uploaded_file
) -> None:
    """Test that the upload endpoint is called correctly with FileAlreadyExistsError."""
    file_path = tmp_path.joinpath("file.txt")
    file_path.write_text("content")
    file_model, file_content = mock_uploaded_file
    file_model.file_path = file_path
    error = FileAlreadyExistsError(file_model.name)

    def _mock_add_uploaded_file(*_, **__):
        raise error

    monkeypatch.setattr(IOHelper, "save_uploaded_file", lambda *_, **__: file_model)
    monkeypatch.setattr(DatabaseHelper, "add_uploaded_file", _mock_add_uploaded_file)

    response = client.post(
        "/upload",
        data={
            "file": file_content,
            "name": "name",
            "sha256": "sha256",
            "layer": "layer",
            "field": "field",
            "band": "band",
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json == {"error": str(error)}
    assert not file_path.exists()


def test_calcculate_intersection(client, monkeypatch) -> None:
    """Test that the calculate_intersection endpoint is called correctly."""
    job_id = "job_id"
    vector = File(
        name="name1",
        kind="vector",
        sha256="sha2561",
        file_path="file_path1",
        geometry_type="Polygon",
    )
    raster = File(
        name="name2",
        kind="vector",
        sha256="sha2562",
        file_path="file_path2",
        geometry_type="Polygon",
    )
    monkeypatch.setattr(
        DatabaseHelper,
        "get_intersection",
        lambda *_, **__: (vector, raster),
    )
    monkeypatch.setattr(
        RedisHelper, "enqueue_intersection_job", lambda *_, **__: _MockJob(job_id)
    )

    response = client.post(
        "/calculate_intersection", data={"first": "first", "second": "second"}
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    assert f"/status/{job_id}" in response.data.decode()


def test_calculate_intersection_with_intersection_with_self(
    client, monkeypatch
) -> None:
    """Test that the calculate_intersection endpoint is called correctly with
    IntersectionWithSelfError."""
    error = IntersectionWithSelfError("first")
    monkeypatch.setattr(
        DatabaseHelper, "get_intersection", lambda *_, **__: Intersection()
    )
    monkeypatch.setattr(RedisHelper, "enqueue_intersection_job", lambda *_, **__: None)

    response = client.post(
        "/calculate_intersection", data={"first": "first", "second": "first"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json == {"error": str(error)}


def test_calculate_intersection_with_invalid_intersection_file_types(
    client, monkeypatch
) -> None:
    """Test that the calculate_intersection endpoint is called correctly with
    InvalidIntersectionFileTypesError."""
    vector = File(name="name1", kind="vector", sha256="sha2561", file_path="file_path1")
    raster = File(name="name2", kind="raster", sha256="sha2562", file_path="file_path2")
    error = InvalidIntersectionFileTypesError(
        vector.sha256, vector.kind, raster.sha256, raster.kind
    )
    monkeypatch.setattr(
        DatabaseHelper,
        "get_intersection",
        lambda *_, **__: (vector, raster),
    )
    monkeypatch.setattr(RedisHelper, "enqueue_intersection_job", lambda *_, **__: None)

    response = client.post(
        "/calculate_intersection",
        data={"first": vector.sha256, "second": raster.sha256},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json == {"error": str(error)}


def test_calculate_intersection_with_invalid_intersection_geometry_type(
    client, monkeypatch
) -> None:
    """Test that the calculate_intersection endpoint is called correctly with
    InvalidIntersectionGeometryTypeError."""
    vector = File(
        name="name1",
        kind="vector",
        sha256="sha2561",
        file_path="file_path1",
        geometry_type="Point",
    )
    raster = File(
        name="name2",
        kind="vector",
        sha256="sha2562",
        file_path="file_path2",
        geometry_type="Point",
    )
    error = InvalidIntersectionGeometryTypeError(
        vector.sha256, vector.kind, raster.sha256, raster.kind
    )
    monkeypatch.setattr(
        DatabaseHelper,
        "get_intersection",
        lambda *_, **__: (vector, raster),
    )
    monkeypatch.setattr(RedisHelper, "enqueue_intersection_job", lambda *_, **__: None)

    response = client.post(
        "/calculate_intersection",
        data={"first": vector.sha256, "second": raster.sha256},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json == {"error": str(error)}


def test_calculate_rastert_stats(client, monkeypatch) -> None:
    """Test that the calculate_raster_stats endpoint is called correctly."""
    job_id = "job_id"
    vector = File(name="name1", kind="vector", sha256="sha2561", file_path="file_path1")
    raster = File(name="name2", kind="raster", sha256="sha2562", file_path="file_path2")
    monkeypatch.setattr(
        DatabaseHelper, "get_raster_stats", lambda *_, **__: (vector, raster)
    )
    monkeypatch.setattr(
        RedisHelper, "enqueue_raster_stats_job", lambda *_, **__: _MockJob(job_id)
    )
    monkeypatch.setattr("flask.send_file", lambda *_, **__: None)

    response = client.post(
        "/calculate_raster_stats",
        data={"vector": vector.sha256, "raster": raster.sha256, "field": "name"},
    )
    assert f"/status/{job_id}" in response.data.decode()
    assert response.status_code == HTTPStatus.ACCEPTED


def test_calculate_raster_stats_invalid_rasterstats_file_types(
    client, monkeypatch
) -> None:
    """Test that the calculate_raster_stats endpoint is called correctly with
    InvalidRasterstatsFileTypesError."""
    vector = File(name="name1", kind="raster", sha256="sha2561", file_path="file_path1")
    raster = File(name="name2", kind="vector", sha256="sha2562", file_path="file_path2")
    error = InvalidRasterstatsFileTypesError(
        vector.sha256, vector.kind, raster.sha256, raster.kind
    )
    monkeypatch.setattr(
        DatabaseHelper, "get_raster_stats", lambda *_, **__: (vector, raster)
    )
    monkeypatch.setattr(RedisHelper, "enqueue_raster_stats_job", lambda *_, **__: None)
    monkeypatch.setattr("flask.send_file", lambda *_, **__: None)

    response = client.post(
        "/calculate_raster_stats",
        data={"vector": vector.sha256, "raster": raster.sha256},
    )
    assert response.json == {"error": str(error)}
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_calculate_remaining(client, monkeypatch) -> None:
    """Test that the calculate_intersection endpoint is called correctly."""
    job_id = "job_id"
    monkeypatch.setattr(
        DatabaseHelper,
        "get_remaining",
        lambda *_, **__: Remaining(intersection=Intersection()),
    )
    monkeypatch.setattr(
        RedisHelper, "enqueue_remaining_job", lambda *_, **__: _MockJob("job_id")
    )

    response = client.post(
        "/calculate_remaining", data={"first": "first", "second": "second"}
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    assert f"/status/{job_id}" in response.data.decode()
