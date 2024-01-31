"""Test cases for the __IOHelper__ class."""
import pytest

from pandarus_remote.errors import InvalidSpatialDatasetError, NoneReproducibleHashError

from ... import FILE_RASTER, FILE_TEXT, FILE_VECTOR1


def test_data_dir(io_helper) -> None:
    """Test the IOHelper.data_dir property."""
    assert io_helper.data_dir.exists()


def test_logs_dir(io_helper) -> None:
    """Test the IOHelper.logs_dir property."""
    assert io_helper.logs_dir.exists()


def test_uploads_dir(io_helper) -> None:
    """Test the IOHelper.uploads_dir property."""
    assert io_helper.uploads_dir.exists()


def test_intersections_dir(io_helper) -> None:
    """Test the IOHelper.intersections_dir property."""
    assert io_helper.intersections_dir.exists()


def test_raster_stats_dir(io_helper) -> None:
    """Test the IOHelper.raster_stats_dir property."""
    assert io_helper.raster_stats_dir.exists()


def test_remaining_dir(io_helper) -> None:
    """Test the IOHelper.remaining_dir property."""
    assert io_helper.remaining_dir.exists()


def test_save_uploaded_file_vector(assert_upload_file) -> None:
    """Test the IOHelper.save_uploaded_file method with vector input."""
    assert_upload_file(FILE_VECTOR1)


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
