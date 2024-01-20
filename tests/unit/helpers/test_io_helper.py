"""Test cases for the __IOHelper__ class."""
import pytest

from pandarus_remote.errors import InvalidSpatialDatasetError, NoneReproducibleHashError
from pandarus_remote.helpers import IOHelper

from ... import FILE_RASTER, FILE_TEXT, FILE_VECTOR


def test_data_dir(mock_appdirs, assert_path) -> None:
    """Test the IOHelper.data_dir property."""
    data_dir, _ = mock_appdirs
    assert_path(data_dir, IOHelper().data_dir)


def test_logs_dir(mock_appdirs, assert_path) -> None:
    """Test the IOHelper.logs_dir property."""
    _, logs_dir = mock_appdirs
    assert_path(logs_dir, IOHelper().logs_dir)


def test_uploads_dir(mock_appdirs, assert_path) -> None:
    """Test the IOHelper.uploads_dir property."""
    data_dir, _ = mock_appdirs
    uploads_sub_dir = "uploads"
    uploads_sub_dir_path = data_dir / uploads_sub_dir
    assert_path(
        uploads_sub_dir_path, IOHelper(uploads_sub_dir=uploads_sub_dir).uploads_dir
    )


def test_intersections_dir(mock_appdirs, assert_path) -> None:
    """Test the IOHelper.intersections_dir property."""
    data_dir, _ = mock_appdirs
    intersections_sub_dir = "intersections"
    intersections_sub_dir_path = data_dir / intersections_sub_dir
    assert_path(
        intersections_sub_dir_path,
        IOHelper(intersections_sub_dir=intersections_sub_dir).intersections_dir,
    )


def test_raster_stats_dir(mock_appdirs, assert_path) -> None:
    """Test the IOHelper.raster_stats_dir property."""
    data_dir, _ = mock_appdirs
    raster_stats_sub_dir = "raster_stats"
    raster_stats_sub_dir_path = data_dir / raster_stats_sub_dir
    assert_path(
        raster_stats_sub_dir_path,
        IOHelper(raster_stats_sub_dir=raster_stats_sub_dir).raster_stats_dir,
    )


def test_remaining_dir(mock_appdirs, assert_path) -> None:
    """Test the IOHelper.remaining_dir property."""
    data_dir, _ = mock_appdirs
    remaining_sub_dir = "remaining"
    remaining_sub_dir_path = data_dir / remaining_sub_dir
    assert_path(
        remaining_sub_dir_path,
        IOHelper(remaining_sub_dir=remaining_sub_dir).remaining_dir,
    )


def test_save_uploaded_file_vector(assert_upload_file) -> None:
    """Test the IOHelper.save_uploaded_file method with vector input."""
    assert_upload_file(FILE_VECTOR)


def test_save_uploaded_file_raster(assert_upload_file) -> None:
    """Test the IOHelper.save_uploaded_file method with raster input."""
    assert_upload_file(FILE_RASTER)


def test_save_uploaded_file_text(assert_upload_file) -> None:
    """Test the IOHelper.save_uploaded_file method with text input."""
    with pytest.raises(InvalidSpatialDatasetError):
        assert_upload_file(FILE_TEXT)


def test_save_uploaded_file_none_reproducible_hash(assert_upload_file) -> None:
    """Test the IOHelper.save_uploaded_file method with none-reproducible hash."""
    with pytest.raises(NoneReproducibleHashError):
        assert_upload_file(FILE_RASTER, hash_func=lambda _: "")
