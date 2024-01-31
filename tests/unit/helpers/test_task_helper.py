"""Test cases for the __TaskHelper__ class."""
from pandarus_remote.helpers import TaskHelper
from pandarus_remote.models import File, Intersection, RasterStats, Remaining

from ... import FILE_VECTOR1


def test_n_cpu_default() -> None:
    """Test that the default number of CPUs is 1."""
    assert TaskHelper().n_cpu == 1


def test_n_cpu_custom(monkeypatch) -> None:
    """Test that the number of CPUs can be set with an environment variable."""
    monkeypatch.setenv("PANDARUS_CPUS", "4")
    assert TaskHelper().n_cpu == 4


def test_export_format_default() -> None:
    """Test that the default export format is GeoJSON."""
    assert TaskHelper().export_format == "GeoJSON"


def test_export_format_custom(monkeypatch) -> None:
    """Test that the export format can be set with an environment variable."""
    monkeypatch.setenv("PANDARUS_EXPORT_FORMAT", "Shapefile")
    assert TaskHelper().export_format == "Shapefile"


def test_intersect_task(monkeypatch, database_helper) -> None:
    """Test that the intersect_task runs correctly."""
    monkeypatch.setattr(
        "pandarus_remote.helpers.intersect",
        lambda *_, **__: (FILE_VECTOR1, "data_path"),
    )
    monkeypatch.setattr(
        "pandarus_remote.helpers.intersections_from_intersection",
        lambda *_, **__: ("data_path1", "data_path2"),
    )
    database_helper(inserted_files=2)
    TaskHelper().intersect_task(
        File.get(File.id == 1),
        File.get(File.id == 2),
    )
    assert Intersection.select().count(None) == 3
    assert Intersection.select().first(None).first_file.id == 1
    assert Intersection.select().first(None).second_file.id == 2
    assert Intersection.select().first(None).data_file_path == "data_path"
    assert Intersection.select().first(None).vector_file_path == str(FILE_VECTOR1)


def test_raster_stats_task(monkeypatch, database_helper) -> None:
    """Test that the raster_stats_task runs correctly."""
    monkeypatch.setattr(
        "pandarus_remote.helpers.raster_statistics",
        lambda *_, **__: "data_path",
    )

    database_helper(inserted_files=2, insert_intersections=True)
    TaskHelper().raster_stats_task(
        File.get(File.id == 1),
        File.get(File.id == 2),
        1,
    )
    assert RasterStats.select().count(None) == 1
    assert RasterStats.select().first(None).vector_file.id == 1
    assert RasterStats.select().first(None).raster_file.id == 2
    assert RasterStats.select().first(None).output_file_path == "data_path"


def test_remaining_task(monkeypatch, database_helper) -> None:
    """Test that the remaining_task runs correctly."""
    monkeypatch.setattr(
        "pandarus_remote.helpers.calculate_remaining",
        lambda *_, **__: "data_path",
    )

    database_helper(inserted_files=2, insert_intersections=True)
    TaskHelper().remaining_task(1)
    assert Remaining.select().count(None) == 1
    assert Remaining.select().first(None).intersection.id == 1
    assert Remaining.select().first(None).data_file_path == "data_path"
