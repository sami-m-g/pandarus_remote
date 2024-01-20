"""Test cases for the __RedisHelper__ class."""
import pytest
from rq.job import Job

from pandarus_remote.errors import JobNotFoundError
from pandarus_remote.helpers import RedisHelper, TaskHelper
from pandarus_remote.models import File, Intersection


def test_get_job_status_not_exists(mock_redis) -> None:
    """Test the RedisHelper.get_job_status method but job doesn't exist."""
    with pytest.raises(JobNotFoundError) as jnfe:
        RedisHelper(redis_connection=mock_redis).get_job_status("job_id")
        assert "job_id" in str(jnfe)


def test_get_job_status_exists(mock_redis) -> None:
    """Test the RedisHelper.get_job_status method and job exists."""
    job_id = "job_id"
    job = Job.create(func=lambda: None, connection=mock_redis, id=job_id)
    redis_helper = RedisHelper(redis_connection=mock_redis)
    redis_helper.queue.enqueue_job(job)
    assert redis_helper.get_job_status(job_id) == {
        "status": "queued",
        "result": None,
    }


def test_enqueue_interesect_job(mock_redis, database_helper) -> None:
    """Test the RedisHelper.enqueue_intersect_job method."""
    database_helper(inserted_files=2)
    redis_helper = RedisHelper(redis_connection=mock_redis)
    assert (
        redis_helper.enqueue_intersect_job(
            File.get(File.id == 1),
            File.get(File.id == 2),
        ).func_name
        == TaskHelper().intersect_task.__name__
    )


def test_enqueue_raster_stats_job(mock_redis, database_helper) -> None:
    """Test the RedisHelper.enqueue_raster_stats_job method."""
    database_helper(inserted_files=2)
    redis_helper = RedisHelper(redis_connection=mock_redis)
    assert (
        redis_helper.enqueue_raster_stats_job(
            File.get(File.id == 1),
            File.get(File.id == 2),
            1,
        ).func_name
        == TaskHelper().raster_stats_task.__name__
    )


def test_enqueue_remaining_job(mock_redis, database_helper) -> None:
    """Test the RedisHelper.enqueue_remaining_job method."""
    database_helper(inserted_files=2, insert_intersections=True)
    redis_helper = RedisHelper(redis_connection=mock_redis)
    assert (
        redis_helper.enqueue_remaining_job(
            Intersection.get(Intersection.id == 1),
        ).func_name
        == TaskHelper().remaining_task.__name__
    )
