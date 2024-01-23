"""Test cases for the __RedisHelper__ class."""
import pytest

from pandarus_remote.errors import JobNotFoundError
from pandarus_remote.models import File, Intersection


def test_get_job_status_not_exists(redis_helper) -> None:
    """Test the RedisHelper.get_job_status method but job doesn't exist."""
    with pytest.raises(JobNotFoundError) as jnfe:
        redis_helper.get_job_status("job_id")
        assert "job_id" in str(jnfe)


def test_get_job_status_exists(redis_helper) -> None:
    """Test the RedisHelper.get_job_status method and job exists."""
    job = redis_helper.queue.enqueue(lambda: None)
    assert redis_helper.get_job_status(job.id) == {
        "status": "queued",
        "result": None,
    }


def test_enqueue_interesect_job(redis_helper) -> None:
    """Test the RedisHelper.enqueue_intersection_job method."""
    file1 = File(name="name1", kind="kind1", sha256="sha2561")
    file2 = File(name="name2", kind="kind2", sha256="sha2562")
    job = redis_helper.enqueue_intersection_job(file1, file2)
    assert job.args[0].name == file1.name
    assert job.args[1].name == file2.name


def test_enqueue_raster_stats_job(redis_helper) -> None:
    """Test the RedisHelper.enqueue_raster_stats_job method."""
    file1 = File(name="name1", kind="kind1", sha256="sha2561")
    file2 = File(name="name2", kind="kind2", sha256="sha2562")
    job = redis_helper.enqueue_raster_stats_job(file1, file2, 1)
    assert job.args[0].name == file1.name
    assert job.args[1].name == file2.name
    assert job.args[2] == 1


def test_enqueue_remaining_job(redis_helper) -> None:
    """Test the RedisHelper.enqueue_remaining_job method."""
    intersection = Intersection(
        data_file_path="data_file_path", vector_file_path="vector_file_path"
    )
    assert (
        redis_helper.enqueue_remaining_job(intersection).args[0].data_file_path
        == intersection.data_file_path
    )
