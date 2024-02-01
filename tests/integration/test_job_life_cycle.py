"""Integration test for the job life cycle:
    1. Check the catalog to be empty.
    2. Upload a file(vector1).
    3. Upload a file(vector2).
    4. Upload a file(raster).
    5. Run a calculation(raster_stats).
    6. Run a calculation(intersection).
    7. Run a calculation(remaining).
"""
import os

import pytest
from pandarus import intersect
from pandarus.utils.io import sha256_file

from .. import FILE_RASTER, FILE_VECTOR1, FILE_VECTOR2
from .utils import check_catalog, run_calculation, upload_file


@pytest.mark.filterwarnings(
    "ignore:The `pop_connection` function is deprecated.*:DeprecationWarning",
    "ignore:The `push_connection` function is deprecated.*:DeprecationWarning",
)
def test_job_life_cycle(client, tmpdir) -> None:
    """Test the job life cycle."""

    catalog = {
        "files": [],
        "intersections": [],
        "remainings": [],
        "raster_stats": [],
    }

    # 1. Check the catalog to be empty.
    check_catalog(client, catalog)

    # 2. Upload a file(vector1).
    vector1_sha256 = upload_file(client, FILE_VECTOR1, "vector", catalog)

    # 3. Upload a file(vector2).
    vector2_sha256 = upload_file(client, FILE_VECTOR2, "vector", catalog)

    # 4. Upload a file(raster).
    raster_sha256 = upload_file(client, FILE_RASTER, "raster", catalog)

    # 5. Run a calculation(raster_stats).
    catalog["raster_stats"].append(
        {
            "vector_sha256": vector1_sha256,
            "raster_sha256": raster_sha256,
        }
    )
    run_calculation(
        client,
        {
            "vector": vector1_sha256,
            "raster": raster_sha256,
        },
        "raster_stats",
        catalog,
    )

    # 6. Run a calculation(intersection).
    intersection_path, _ = intersect(
        FILE_VECTOR1,
        "name",
        FILE_VECTOR2,
        "name",
        out_dir=tmpdir,
    )
    intersection_sha256 = sha256_file(intersection_path)
    catalog["files"].append(
        {
            "name": os.path.basename(intersection_path),
            "kind": "vector",
            "sha256": intersection_sha256,
        }
    )
    catalog["intersections"].extend(
        [
            {
                "first_file_sha256": vector1_sha256,
                "second_file_sha256": vector2_sha256,
            },
            {
                "first_file_sha256": intersection_sha256,
                "second_file_sha256": vector1_sha256,
            },
            {
                "first_file_sha256": intersection_sha256,
                "second_file_sha256": vector2_sha256,
            },
        ]
    )
    run_calculation(
        client,
        {
            "first": vector1_sha256,
            "second": vector2_sha256,
        },
        "intersection",
        catalog,
    )

    # 7. Run a calculation(remaining).
    catalog["remainings"].append(
        {
            "first_file_sha256": vector1_sha256,
            "second_file_sha256": vector2_sha256,
        }
    )
    run_calculation(
        client,
        {
            "first": vector1_sha256,
            "second": vector2_sha256,
        },
        "remaining",
        catalog,
    )
