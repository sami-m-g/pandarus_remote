"""Test cases for the __DatabaseHelper__ class."""
import pytest

from pandarus_remote.errors import (
    FileAlreadyExistsError,
    NoEntryFoundError,
    ResultAlreadyExistsError,
)
from pandarus_remote.models import File, Intersection


def test_files(database_helper) -> None:
    """Test the DatabaseHelper.files property."""
    assert database_helper().files == []

    assert database_helper(inserted_files=2).files == [
        ("name1", "kind1", "sha2561"),
        ("name2", "kind2", "sha2562"),
    ]


def test_intersections(database_helper) -> None:
    """Test the DatabaseHelper.intersections property."""
    assert database_helper().intersections == []

    assert database_helper(
        inserted_files=2, insert_intersections=True
    ).intersections == [
        ("sha2561", "sha2562"),
        ("sha2562", "sha2561"),
    ]


def test_raster_stats(database_helper) -> None:
    """Test the DatabaseHelper.raster_stats property."""
    assert database_helper().raster_stats == []

    helper = database_helper(
        inserted_files=2, insert_intersections=True, insert_raster_stats=True
    )
    assert helper.raster_stats == [
        ("sha2561", "sha2562"),
        ("sha2562", "sha2561"),
    ]


def test_remaining(database_helper) -> None:
    """Test the DatabaseHelper.remaining property."""
    assert database_helper().remaining == []

    assert database_helper(
        inserted_files=2, insert_intersections=True, insert_remaining=True
    ).remaining == [
        ("sha2561", "sha2562"),
        ("sha2562", "sha2561"),
    ]


def test_catalog(database_helper) -> None:
    """Test the DatabaseHelper.catalog property."""
    assert database_helper().catalog == {
        "files": [],
        "intersections": [],
        "raster_stats": [],
        "remaining": [],
    }

    helper = database_helper(
        inserted_files=2,
        insert_intersections=True,
        insert_remaining=True,
        insert_raster_stats=True,
    )
    assert helper.catalog == {
        "files": [
            ("name1", "kind1", "sha2561"),
            ("name2", "kind2", "sha2562"),
        ],
        "intersections": [
            ("sha2561", "sha2562"),
            ("sha2562", "sha2561"),
        ],
        "raster_stats": [
            ("sha2561", "sha2562"),
            ("sha2562", "sha2561"),
        ],
        "remaining": [
            ("sha2561", "sha2562"),
            ("sha2562", "sha2561"),
        ],
    }


def test_validate_query_file1_id_not_found(database_helper) -> None:
    """Test the DatabaseHelper.validate_query method with file1_id not found."""
    with pytest.raises(NoEntryFoundError) as nefe:
        database_helper().validate_query("sha2561", "sha2562")
        assert "[sha2561]" in str(nefe)


def test_validate_query_file2_id_not_found(database_helper) -> None:
    """Test the DatabaseHelper.validate_query method  with file2_id not found."""
    with pytest.raises(NoEntryFoundError) as nefe:
        database_helper(inserted_files=1).validate_query("sha2561", "sha2562")
        assert "[sha2562]" in str(nefe)


def test_validate_query_should_exist_and_exists(database_helper) -> None:
    """Test the DatabaseHelper.validate_query method with should_exist=True and it
    exists."""
    intersection = database_helper(
        inserted_files=2, insert_intersections=True
    ).validate_query(
        "sha2561",
        "sha2562",
        lambda first_file, second_file: Intersection.get(
            (Intersection.first_file == first_file)
            & (Intersection.second_file == second_file)
        ),
        should_exist=True,
    )
    intersection.first_file.sha256 = "sha2561"
    intersection.second_file.sha256 = "sha2562"


def test_validate_query_should_exist_and_does_not_exists(database_helper) -> None:
    """Test the DatabaseHelper.validate_query method with should_exist=True and it
    doesn't exist."""
    with pytest.raises(NoEntryFoundError) as nefe:
        database_helper(inserted_files=2).validate_query(
            "sha2561",
            "sha2562",
            lambda first_file, second_file: Intersection.get(
                (Intersection.first_file == first_file)
                & (Intersection.second_file == second_file)
            ),
            should_exist=True,
        )
        assert "[1, 2]" in str(nefe)


def test_validate_query_result_should_not_exist_and_exists(database_helper) -> None:
    """Test the DatabaseHelper.validate_query method with should_exist=False and it
    exists."""
    with pytest.raises(ResultAlreadyExistsError) as raee:
        database_helper(inserted_files=2, insert_intersections=True).validate_query(
            "sha2561",
            "sha2562",
            lambda first_file, second_file: Intersection.get(
                (Intersection.first_file == first_file)
                & (Intersection.second_file == second_file)
            ),
            should_exist=False,
        )
        assert "[1, 2]" in str(raee)


def test_validate_query_result_should_not_exist_and_not_exists(database_helper) -> None:
    """Test the DatabaseHelper.validate_query method with should_exist=False and
    it doesn't exist."""
    files = database_helper(inserted_files=2).validate_query(
        "sha2561",
        "sha2562",
        lambda first_file, second_file: Intersection.get(
            (Intersection.first_file == first_file)
            & (Intersection.second_file == second_file)
        ),
        should_exist=False,
    )
    assert files[0].sha256 == "sha2561"
    assert files[1].sha256 == "sha2562"


def test_get_raster_stats(database_helper) -> None:
    """Test the DatabaseHelper.get_raster_stats method."""
    assert (
        database_helper(
            inserted_files=2, insert_intersections=True, insert_raster_stats=True
        )
        .get_raster_stats("sha2561", "sha2562")
        .output_file_path
        == "output_path1"
    )


def test_get_intersection(database_helper) -> None:
    """Test the DatabaseHelper.get_intersection method."""
    assert (
        database_helper(inserted_files=2, insert_intersections=True)
        .get_intersection("sha2561", "sha2562")
        .data_file_path
        == "data_path1"
    )


def test_get_remaining_exists(database_helper) -> None:
    """Test the DatabaseHelper.get_remaining method and results exists."""
    assert (
        database_helper(
            inserted_files=2, insert_intersections=True, insert_remaining=True
        )
        .get_remaining("sha2561", "sha2562")
        .data_file_path
        == "data_path1"
    )


def test_get_remaining_not_exists(database_helper) -> None:
    """Test the DatabaseHelper.get_remaining method and result doesn't exist."""
    with pytest.raises(NoEntryFoundError) as nefe:
        database_helper(inserted_files=2, insert_intersections=True).get_remaining(
            "sha2561", "sha2562"
        )
        assert "[sha2561]" in str(nefe)


def test_add_uploaded_file_not_exists(database_helper) -> None:
    """Test the DatabaseHelper.add_uploaded_file method and file doesn't exist."""
    database_helper().add_uploaded_file(
        File(
            name="name",
            kind="kind",
            sha256="sha256",
            file_path="file_path",
        )
    )
    assert File.select().where(File.sha256 == "sha256").exists()


def test_add_uploaded_file_exists(database_helper) -> None:
    """Test the DatabaseHelper.add_uploaded_file method and file exists."""
    with pytest.raises(FileAlreadyExistsError) as faee:
        helper = database_helper(inserted_files=1)
        helper.add_uploaded_file(File.select().first(None))
        assert "name" in str(faee)
