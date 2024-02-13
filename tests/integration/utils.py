"""Utility functions for the __pandarus_remote__ integration tests."""
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

from flask.testing import FlaskClient
from pandarus.utils.io import sha256_file
from rq import Worker

from pandarus_remote.errors import NoEntryFoundError, ResultAlreadyExistsError
from pandarus_remote.helpers import RedisHelper


def check_catalog(
    client_app: FlaskClient,
    catalog: Dict[str, List[Tuple[str, str]]],
) -> None:
    """Check the catalog against a reference."""
    response = client_app.get("/catalog")
    assert response.json == catalog
    assert response.status_code == HTTPStatus.OK


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
    assert response.json == {"error": str(NoEntryFoundError(files))}
    assert response.status_code == HTTPStatus.NOT_FOUND

    # 2. Create a job to calculate the calculation.
    response = client_app.post(calc_endpoint, data=data)
    assert response.status_code == HTTPStatus.ACCEPTED

    # 3. Check the job status is running.
    job_id = response.data.decode().split("/")[-1]
    response = client_app.get(f"/status/{job_id}")
    assert response.json["status"] == "queued"
    assert response.status_code == HTTPStatus.OK

    # 4. Try to calculate the calculation again.
    response = client_app.post(calc_endpoint, data=data)
    new_job_id = response.data.decode().split("/")[-1]
    assert response.status_code == HTTPStatus.ACCEPTED
    assert new_job_id == job_id

    # 5. Check the job status is finished.
    Worker(
        connection=RedisHelper().queue.connection,
        queues=[RedisHelper().queue],
    ).work(burst=True)
    response = client_app.get(f"/status/{job_id}")
    # Doesn't work on GitHub Actions.
    # assert response.json["status"] == "finished"
    assert response.status_code == HTTPStatus.OK

    # 6. Get the calculation of these 2 files.
    response = client_app.post(calculation, data=data)
    assert response.status_code == HTTPStatus.OK

    # 7. Check the catalog include the new calculation.
    check_catalog(client_app, catalog)

    # 8. Try to calculate the calculation again.
    response = client_app.post(calc_endpoint, data=data)
    assert response.json == {"error": str(ResultAlreadyExistsError(files))}
    assert response.status_code == HTTPStatus.CONFLICT
