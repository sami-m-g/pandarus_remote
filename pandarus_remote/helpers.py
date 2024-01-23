"""Helpers for the __pandarus_remote__ web service."""
import os
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import appdirs
import fiona
from pandarus import (
    calculate_remaining,
    intersect,
    intersections_from_intersection,
    raster_statistics,
)
from pandarus.errors import UnknownDatasetTypeError
from pandarus.utils.conversion import check_dataset_type
from pandarus.utils.io import sha256_file
from peewee import DoesNotExist, SqliteDatabase
from redis import Redis
from rq import Queue
from rq.job import Job
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from .errors import (
    FileAlreadyExistsError,
    InvalidSpatialDatasetError,
    JobNotFoundError,
    NoEntryFoundError,
    NoneReproducibleHashError,
    ResultAlreadyExistsError,
)
from .models import BaseModel, File, Intersection, RasterStats, Remaining
from .utils import create_if_not_exists, loggable


class IOHelper:
    """Helper class for IO operations."""

    _instance: "IOHelper" = None

    def __new__(cls, *_: Tuple[Any], **__: Dict[str, Any]) -> "IOHelper":
        if not cls._instance:
            cls._instance = super(IOHelper, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        app_name: str = "pandarus_remote",
        app_author: str = "pandarus_remote",
        uploads_sub_dir: str = "uploads",
        intersections_sub_dir: str = "intersections",
        raster_stats_sub_dir: str = "raster_stats",
        remaining_sub_dir: str = "remaining",
    ) -> None:
        self.app_name = app_name
        self.app_author = app_author
        self.uploads_sub_dir = uploads_sub_dir
        self.intersections_sub_dir = intersections_sub_dir
        self.raster_stats_sub_dir = raster_stats_sub_dir
        self.remaining_sub_dir = remaining_sub_dir

    @property
    @create_if_not_exists
    def data_dir(self) -> Path:
        """Return the data directory."""
        return Path(appdirs.user_data_dir(self.app_name, self.app_author))

    @property
    @create_if_not_exists
    def logs_dir(self) -> Path:
        """Return the logs directory."""
        return Path(appdirs.user_log_dir(self.app_name, self.app_author))

    @property
    @create_if_not_exists
    def uploads_dir(self) -> Path:
        """Return the uploads directory."""
        return self.data_dir / self.uploads_sub_dir

    @property
    @create_if_not_exists
    def intersections_dir(self) -> Path:
        """Return the intersections directory."""
        return self.data_dir / self.intersections_sub_dir

    @property
    @create_if_not_exists
    def raster_stats_dir(self) -> Path:
        """Return the raster_stats directory."""
        return self.data_dir / self.raster_stats_sub_dir

    @property
    @create_if_not_exists
    def remaining_dir(self) -> Path:
        """Return the remaining directory."""
        return self.data_dir / self.remaining_sub_dir

    def save_uploaded_file(
        self,
        file: FileStorage,
        name: str,
        file_hash: str,
        layer: Optional[str] = None,
        field: Optional[str] = None,
        band: Optional[str] = None,
    ) -> File:
        """Save an uploaded file. Raises InvalidSpatialDatasetError if the file is not a
        valid spatial dataset. Raises NoneReproducibleHashError if the file_hash is not
        reproducible."""
        secure_name = secure_filename(name)
        new_name = f"{uuid.uuid4().hex}.{secure_name}"
        file_path: Path = self.uploads_dir / new_name
        file.save(file_path)

        try:
            kind = check_dataset_type(file_path)
        except UnknownDatasetTypeError as udte:
            file_path.unlink()
            raise InvalidSpatialDatasetError(name) from udte
        if kind == "vector":
            band = None
            with fiona.open(file_path) as src:
                geom_type = src.meta["schema"]["geometry"]
        else:  # kind == "raster"
            layer = field = geom_type = None

        our_hash = sha256_file(file_path)
        if our_hash != file_hash:
            file_path.unlink()
            raise NoneReproducibleHashError(name)

        return File(
            file_path=file_path,
            name=new_name,
            sha256=our_hash,
            band=band,
            layer=layer,
            field=field,
            kind=kind,
            geometry_type=geom_type,
        )


class DatabaseHelper:
    """Helper class for database operations."""

    _instance: "DatabaseHelper" = None

    def __new__(cls, *_, **__) -> None:
        if not cls._instance:
            cls._instance = super(DatabaseHelper, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        database: str = IOHelper().data_dir / "pandarus_remote.db",
    ) -> None:
        self._database = SqliteDatabase(database)
        self._database.bind([File, Intersection, RasterStats, Remaining])
        self._database.create_tables([File, Intersection, RasterStats, Remaining])

    @property
    def files(self) -> List[Tuple[str, str, str]]:
        """Return a list of files."""
        return [(obj.name, obj.kind, obj.sha256) for obj in File.select()]

    @property
    def intersections(self) -> List[Tuple[str, str]]:
        """Return a list of intersections."""
        return [
            (obj.first_file.sha256, obj.second_file.sha256)
            for obj in Intersection.select()
        ]

    @property
    def remaining(self) -> List[Tuple[str, str]]:
        """Return a list of remaining."""
        return [
            (obj.intersection.first_file.sha256, obj.intersection.second_file.sha256)
            for obj in Remaining.select()
        ]

    @property
    def raster_stats(self) -> List[Tuple[str, str]]:
        """Return a list of raster_stats."""
        return [
            (obj.vector_file.sha256, obj.raster_file.sha256)
            for obj in RasterStats.select()
        ]

    @property
    def catalog(self) -> Dict[str, List[Tuple[str, str]]]:
        """Return a catalog of all files, intersections, remaining, and raster_stats."""
        return {
            "files": self.files,
            "intersections": self.intersections,
            "remaining": self.remaining,
            "raster_stats": self.raster_stats,
        }

    @loggable
    def validate_query(
        self,
        file1_hash: str,
        file2_hash: str,
        result_query: Optional[Callable] = None,
        should_exist: bool = True,
    ) -> Union[BaseModel, Tuple[File, File]]:
        """Check if the file1_hash and file2_hash are valid. Raises QueryError if not.
        Returns the result_table entry if it exists and should_exist is True."""
        if not File.select().where(File.sha256 == file1_hash).exists():
            raise NoEntryFoundError([file1_hash])
        file1 = File.get(File.sha256 == file1_hash)

        if not File.select().where(File.sha256 == file2_hash).exists():
            raise NoEntryFoundError([file2_hash])
        file2 = File.get(File.sha256 == file2_hash)

        if result_query is not None:
            try:
                result = result_query(file1, file2)
                if not should_exist:
                    raise ResultAlreadyExistsError([file1_hash, file2_hash])
                return result
            except DoesNotExist as dne:
                if should_exist:
                    raise NoEntryFoundError([file1_hash, file2_hash]) from dne
        return file1, file2

    @loggable
    def get_raster_stats(
        self, vector_sha256: str, raster_sha256: str, should_exist: bool = True
    ) -> RasterStats:
        """Returns a raster_stats ouput path. Raises QueryError if the vector_sha256 or
        raster_sha256 are not found or RasterStats with vector_sha256 and raster_sha256
        combination doesn't exist."""
        return self.validate_query(
            vector_sha256,
            raster_sha256,
            lambda vector_file, raster_file: RasterStats.get(
                (RasterStats.vector_file == vector_file)
                & (RasterStats.raster_file == raster_file)
            ),
            should_exist,
        )

    @loggable
    def get_intersection(
        self, file1_sha256: str, file2_sha256: str, should_exist: bool = True
    ) -> Intersection:
        """Return an intersection. Raises QueryError if the file1_sha256 or file2_sha256
        are not found or Intersection with file1_sha256 and file2_sha256 combination
        doesn't exist."""
        return self.validate_query(
            file1_sha256,
            file2_sha256,
            lambda first_file, second_file: Intersection.get(
                (Intersection.first_file == first_file)
                & (Intersection.second_file == second_file)
            ),
            should_exist,
        )

    @loggable
    def get_remaining(
        self, file1_sha256: str, file2_sha256: str, should_exist: bool = True
    ) -> Remaining:
        """Return a remaining for file1_d and file2_d. Raises QueryError if the
        file1_sha256 or file2_sha256 are not found or Remaining with file1_sha256
        and file2_sha256 combination doesn't exist."""
        intersection_id = self.get_intersection(
            file1_sha256, file2_sha256, should_exist
        ).id
        try:
            return Remaining.get(Remaining.intersection == intersection_id)
        except DoesNotExist as dne:
            raise NoEntryFoundError([intersection_id]) from dne

    @loggable
    def add_uploaded_file(self, file: File) -> None:
        """Add a file to the database. Raises FileAlreadyExistsError if the file already
        exists."""
        if File.select().where(File.sha256 == file.sha256).exists():
            raise FileAlreadyExistsError(file.name)
        file.save()


class RedisHelper:
    """Helper class for redis operations."""

    _instance: "RedisHelper" = None

    def __new__(cls, *_, **__) -> None:
        if not cls._instance:
            cls._instance = super(RedisHelper, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        redis_connection: Redis = Redis(
            host="localhost",
            port=6379,
            db=0,
        ),
    ) -> None:
        self.queue = Queue(connection=redis_connection)

    @loggable
    def get_job_status(self, job_id: str) -> Dict[str, str]:
        """Return the status of a job. Raises `JobNotFoundError` if job is not found."""
        job = self.queue.fetch_job(job_id)
        if job is not None:
            return {"status": job.get_status(), "result": job.return_value()}
        raise JobNotFoundError(job_id)

    @loggable
    def enqueue_intersection_job(self, file1: File, file2: File) -> Job:
        """Enqueues an intersect job."""
        return self.queue.enqueue(
            TaskHelper().intersect_task,
            file1,
            file2,
            IOHelper().intersections_dir,
        )

    @loggable
    def enqueue_raster_stats_job(self, vector: File, raster: File, band: int) -> Job:
        """Enqueues a rasterstats job."""
        return self.queue.enqueue(
            TaskHelper().raster_stats_task,
            vector,
            raster,
            band,
            IOHelper().raster_stats_dir,
        )

    @loggable
    def enqueue_remaining_job(self, intersection: Intersection) -> Job:
        """Enqueues a remaining job."""
        return self.queue.enqueue(
            TaskHelper().remaining_task,
            intersection,
            IOHelper().remaining_dir,
        )


class TaskHelper:
    """Helper class for redis operations."""

    _instance: "TaskHelper" = None

    def __new__(cls, *_, **__) -> None:
        if not cls._instance:
            cls._instance = super(TaskHelper, cls).__new__(cls)
        return cls._instance

    @property
    def n_cpu(self) -> int:
        """Return the number of CPUs to use."""
        try:
            return int(os.environ["PANDARUS_CPUS"])
        except (KeyError, ValueError):
            return 1

    @property
    def export_format(self) -> str:
        """Return the export format."""
        try:
            return os.environ["PANDARUS_EXPORT_FORMAT"]
        except KeyError:
            return "GeoJSON"

    @loggable
    def intersect_task(self, file1: File, file2: File) -> None:
        """Task to intersect two files."""
        vector_path, data = intersect(
            file1.file_path,
            file1.field,
            file2.file_path,
            file2.field,
            out_dir=IOHelper().intersections_dir,
            cpus=self.n_cpu,
            driver=self.export_format,
            log_dir=IOHelper().logs_dir,
        )

        Intersection(
            first_file=file1,
            second_file=file2,
            data_file_path=data,
            vector_file_path=vector_path,
        ).save()
        # Save intersection data files for new spatial scale
        with fiona.open(vector_path) as src:
            geom_type = src.meta["schema"]["geometry"]
        intersection_file = File.create(
            file_path=vector_path,
            name=os.path.basename(vector_path),
            sha256=sha256_file(vector_path),
            band=None,
            layer=None,
            field="id",
            kind="vector",
            geometry_type=geom_type,
        )

        intersect_file1_path, intersect_file2_path = intersections_from_intersection(
            vector_path,
            data,
            IOHelper().intersections_dir,
        )
        Intersection(
            first_file=intersection_file,
            second_file=file1,
            data_file_path=intersect_file1_path,
            vector_file_path=vector_path,
        ).save()
        Intersection(
            first_file=intersection_file,
            second_file=file2,
            data_file_path=intersect_file2_path,
            vector_file_path=vector_path,
        ).save()

    @loggable
    def raster_stats_task(self, vector: File, raster: File, raster_band: int) -> None:
        """Task to compute raster statistics."""
        raster_stats_path = raster_statistics(
            vector.file_path,
            vector.field,
            raster.file_path,
            output_file_path=IOHelper().raster_stats_dir,
            band=raster_band,
        )
        RasterStats(
            vector_file=vector,
            raster_file=raster,
            output_file_path=raster_stats_path,
        ).save()

    @loggable
    def remaining_task(self, intersection_id: int) -> None:
        """Task to compute remaining area."""
        intersection = Intersection.get(Intersection.id == intersection_id)
        source = intersection.first_file
        data_file_path = calculate_remaining(
            source.file_path,
            source.field,
            intersection.vector_file_path,
            out_dir=IOHelper().remaining_dir,
        )
        Remaining(intersection=intersection, data_file_path=data_file_path).save()
