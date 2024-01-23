"""Test suite for the __pandarus_remote__ package."""
from functools import wraps
from io import BytesIO
from pathlib import Path
from typing import Callable, Generator, Tuple

import appdirs
import fakeredis
import pytest
from flask.testing import FlaskClient
from pandarus.utils.io import sha256_file
from werkzeug.datastructures import FileStorage

from pandarus_remote.app import create_app
from pandarus_remote.helpers import DatabaseHelper, IOHelper, RedisHelper
from pandarus_remote.models import File, Intersection, RasterStats, Remaining


@pytest.fixture
def io_helper(tmp_path, monkeypatch) -> Generator[IOHelper, None, None]:
    """Mock the IOHelper."""
    monkeypatch.setattr(appdirs, "user_data_dir", lambda *_, **__: tmp_path / "data")
    monkeypatch.setattr(appdirs, "user_log_dir", lambda *_, **__: tmp_path / "data")
    yield IOHelper("test_pandarus_remote", "test_pandarus_remote")


@pytest.fixture
def assert_upload_file(
    io_helper,  # pylint: disable=redefined-outer-name
) -> Callable[[str, str], None]:
    """Assert that the uploaded file is equal to the expected file."""

    def _assert_upload_file(
        file_path: Path, hash_func: Callable[[Path], str] = sha256_file
    ) -> None:
        uploaded_file_hash = hash_func(file_path)
        with file_path.open("rb") as stream:
            file_storage = FileStorage(
                stream=stream,
                filename=file_path.name,
            )
            file = io_helper.save_uploaded_file(
                file_storage,
                file_path.name,
                uploaded_file_hash,
            )
            assert Path(file.file_path).read_bytes() == file_path.read_bytes()

    return _assert_upload_file


@pytest.fixture
def database_helper() -> Callable[[bool, bool, bool, bool], DatabaseHelper]:
    """Mock a temporary in-memory database and return a DatabaseHelper.
    If insert_files is True, insert two files. If insert_intersections is True,
    insert two intersections. If insert_raster_stats is True, insert two
    raster stats. If insert_remaining is True, insert two remaining."""

    @wraps(database_helper)
    def wrapper(
        inserted_files: int = 0,
        insert_intersections: bool = False,
        insert_raster_stats: bool = False,
        insert_remaining: bool = False,
    ) -> DatabaseHelper:
        helper = DatabaseHelper(":memory:")

        File.insert_many(
            [
                {
                    "name": f"name{inserted_file}",
                    "kind": f"kind{inserted_file}",
                    "sha256": f"sha256{inserted_file}",
                    "file_path": f"path{inserted_file}",
                }
                for inserted_file in range(1, inserted_files + 1)
            ],
            fields=[File.name, File.kind, File.sha256, File.file_path],
        ).execute(None)
        if inserted_files < 2:
            return helper

        if insert_raster_stats:
            RasterStats.insert_many(
                [
                    {
                        "vector_file": 1,
                        "raster_file": 2,
                        "output_file_path": "output_path1",
                    },
                    {
                        "vector_file": 2,
                        "raster_file": 1,
                        "output_file_path": "output_path2",
                    },
                ],
                fields=[
                    RasterStats.vector_file,
                    RasterStats.raster_file,
                    RasterStats.output_file_path,
                ],
            ).execute(None)

        if not insert_intersections:
            return helper
        Intersection.insert_many(
            [
                {
                    "first_file": 1,
                    "second_file": 2,
                    "data_file_path": "data_path1",
                    "vector_file_path": "vector_path1",
                },
                {
                    "first_file": 2,
                    "second_file": 1,
                    "data_file_path": "data_path2",
                    "vector_file_path": "vector_path2",
                },
            ],
            fields=[
                Intersection.first_file,
                Intersection.second_file,
                Intersection.data_file_path,
                Intersection.vector_file_path,
            ],
        ).execute(None)
        if insert_remaining:
            Remaining.insert_many(
                [
                    {"intersection": 1, "data_file_path": "data_path1"},
                    {"intersection": 2, "data_file_path": "data_path2"},
                ],
                fields=[Remaining.intersection, Remaining.data_file_path],
            ).execute(None)
        return helper

    return wrapper


@pytest.fixture
def redis_helper() -> Generator[RedisHelper, None, None]:
    """Mock the RedisHelper."""
    fake_redis = fakeredis.FakeStrictRedis()
    yield RedisHelper(redis_connection=fake_redis)
    fake_redis.flushall()


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Mock the FlaskClient."""
    app = create_app()
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_uploaded_file() -> Generator[Tuple[File, Tuple[BytesIO, str]], None, None]:
    """Mock an uploaded file."""
    file_model = File(
        name="name",
        kind="kind",
        sha256="sha256",
        file_path="file_path",
        band="band",
    )
    file_content = (BytesIO(b"Test"), "test.txt")
    yield file_model, file_content
