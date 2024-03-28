"""Test cases for the __RedisHelper__ class."""

import pytest

from pandarus_remote.errors import JobNotFoundError
from pandarus_remote.helpers import RedisHelper
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


def test_create_task_identifier(redis_helper) -> None:
    """Test the RedisHelper.create_task_identifier method."""

    def _test_func():
        pass

    assert (
        redis_helper.create_task_identifier(
            _test_func,
            "test_arg1",
            "test_arg2",
            test_arg3="test_arg3",
            test_arg4="test_arg4",
        )
        == f"""{_test_func.__name__}: """
        """['test_arg1', 'test_arg2', 'test_arg3', 'test_arg4']"""
    )


def test_enqueue_task_task_does_not_exist(redis_helper, monkeypatch) -> None:
    """Test the RedisHelper.enqueue_task method but task doesn't exist."""
    monkeypatch.setattr(
        RedisHelper, "create_task_identifier", lambda *_, **__: "test_identifier"
    )

    def _test_func():
        pass

    identifier = redis_helper.create_task_identifier(
        _test_func, "test_arg1", "test_arg2"
    )
    assert (
        redis_helper.queue.connection.hget(redis_helper.job_ids_set_name, identifier)
        is None
    )

    job = redis_helper.enqueue_task(_test_func, "test_arg1", "test_arg2")
    assert _test_func.__name__ in job.func_name
    assert job.args == ("test_arg1", "test_arg2")
    assert (
        redis_helper.queue.connection.hget(
            redis_helper.job_ids_set_name, identifier
        ).decode("UTF-8")
        == job.id
    )


def test_enqueue_task_task_exists(redis_helper, monkeypatch) -> None:
    """Test the RedisHelper.enqueue_task method and task exists."""
    monkeypatch.setattr(
        RedisHelper, "create_task_identifier", lambda *_, **__: "test_identifier"
    )

    def _test_func():
        pass

    expected_job = redis_helper.queue.enqueue(lambda: None)
    identifier = redis_helper.create_task_identifier(
        _test_func, "test_arg1", "test_arg2"
    )
    redis_helper.queue.connection.hset(
        redis_helper.job_ids_set_name, identifier, expected_job.id
    )
    assert (
        redis_helper.queue.connection.hget(
            redis_helper.job_ids_set_name, identifier
        ).decode("UTF-8")
        == expected_job.id
    )

    actual_job = redis_helper.enqueue_task(_test_func, "test_arg1", "test_arg2")
    assert actual_job.id == expected_job.id
    assert actual_job.func_name == expected_job.func_name
    assert actual_job.args == expected_job.args


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
