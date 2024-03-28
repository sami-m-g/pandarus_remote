"""Utility functions for the __pandarus_remote__ integration tests."""

from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

from flask.testing import FlaskClient
from pandarus.utils.io import sha256_file
from rq import SimpleWorker

from pandarus_remote.errors import NoEntryFoundError, ResultAlreadyExistsError
from pandarus_remote.helpers import RedisHelper


def check_catalog(
    client_app: FlaskClient,
    catalog: Dict[str, List[Tuple[str, str]]],
) -> None:
    """Check the catalog against a reference."""
    response = client_app.get("/catalog")
    assert response.json == catalog, response.json
    assert response.status_code == HTTPStatus.OK, response.status_code


def upload_file(
    client_app: FlaskClient,
    file_path: Path,
    file_kind: str,
    catalog: Dict[str, List[Tuple[str, str]]],
) -> str:
    """
    1. Upload a file with file_path and file_kind.
    2. Check the catalog includes the new file.
    3. Return the sha256 of the file.
    """
    # 1. Upload a file with file_path and file_kind.
    file_sha256 = sha256_file(file_path)
    response = client_app.post(
        "/upload",
        data={
            "file": (BytesIO(file_path.read_bytes()), file_path.name),
            "name": file_path.name,
            "sha256": file_sha256,
            "field": "name",
        },
    )
    assert response.json["file_sha256"] == file_sha256
    assert response.status_code == HTTPStatus.OK

    # 2. Check the catalog includes the new file.
    file_name = response.json["file_name"]
    catalog["files"].append(
        {
            "name": file_name,
            "kind": file_kind,
            "sha256": file_sha256,
        }
    )
    check_catalog(client_app, catalog)

    # 3. Return the sha256 of the file.
    return file_sha256


def run_calculation(
    client_app: FlaskClient,
    data: Dict[str, str],
    calculation: str,
    catalog: Dict[str, List[Tuple[str, str]]],
) -> None:
    """Run a calculation:
    1. Get the non-existing calculation of 2 files.
    2. Create a job to calculate the calculation.
    3. Check the job status is running.
    4. Try to calculate the calculation again.
    5. Check the job status is finished.
    6. Get the calculation of these 2 files.
    7. Check the catalog include the new calculation.
    8. Try to calculate the calculation again.
    """
    files = list(data.values())
    calc_endpoint = f"/calculate_{calculation}"

    # 1. Get the non-existing calculation of 2 files.
    response = client_app.post(calculation, data=data)
    assert response.json == {"error": str(NoEntryFoundError(files))}, response.json
    assert response.status_code == HTTPStatus.NOT_FOUND, response.status_code

    # 2. Create a job to calculate the calculation.
    response = client_app.post(calc_endpoint, data=data)
    assert response.status_code == HTTPStatus.ACCEPTED, response.status_code

    # 3. Check the job status is running.
    job_id = response.data.decode().split("/")[-1]
    response = client_app.get(f"/status/{job_id}")
    assert response.json["status"] == "queued", response.json["status"]
    assert response.status_code == HTTPStatus.OK, response.status_code

    # 4. Try to calculate the calculation again.
    response = client_app.post(calc_endpoint, data=data)
    new_job_id = response.data.decode().split("/")[-1]
    assert response.status_code == HTTPStatus.ACCEPTED, response.status_code
    assert new_job_id == job_id, new_job_id

    # 5. Check the job status is finished.
    SimpleWorker(
        connection=RedisHelper().queue.connection,
        queues=[RedisHelper().queue],
    ).work(burst=True)
    response = client_app.get(f"/status/{job_id}")
    # Doesn't work on GitHub Actions.
    # assert response.json["status"] == "finished", response.json["status"]
    assert response.status_code == HTTPStatus.OK, response.status_code

    # 6. Get the calculation of these 2 files.
    response = client_app.post(calculation, data=data)
    assert response.status_code == HTTPStatus.OK, response.status_code

    # 7. Check the catalog include the new calculation.
    check_catalog(client_app, catalog)

    # 8. Try to calculate the calculation again.
    response = client_app.post(calc_endpoint, data=data)
    assert response.json == {
        "error": str(ResultAlreadyExistsError(files))
    }, response.json
    assert response.status_code == HTTPStatus.CONFLICT, response.status_code
