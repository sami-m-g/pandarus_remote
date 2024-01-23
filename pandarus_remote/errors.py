"""Errors for the __pandarus_remote__ web service."""
from typing import List


class PandarusRemoteError(Exception):
    """Base class for __pandarus_remote__ errors."""


class JobNotFoundError(PandarusRemoteError):
    """Raised when a redis queue job is not found."""

    def __init__(self, job_id: str) -> None:
        """Initialize the error."""
        super().__init__(f"Job {job_id} not found.")


class QueryError(PandarusRemoteError):
    """Raised when a query parameter is not valid."""


class NoEntryFoundError(QueryError):
    """Raised when no entry is found in the database."""

    def __init__(self, entries_sha256: List[str]) -> None:
        """Initialize the error."""
        super().__init__(f"No entry found for hash(es): {entries_sha256}.")


class ResultAlreadyExistsError(QueryError):
    """Raised when a result already exists in the database."""

    def __init__(self, entries_sha256: List[str]) -> None:
        """Initialize the error."""

        super().__init__(f"Result already exists for hash(es): {entries_sha256}.")


class InvalidSpatialDatasetError(PandarusRemoteError):
    """Raised when a spatial dataset is not valid."""

    def __init__(self, file_name: str) -> None:
        """Initialize the error."""
        super().__init__(
            f"Invalid spatial dataset: {file_name}, must be a vector or a raster."
        )


class NoneReproducibleHashError(PandarusRemoteError):
    """Raised when an uploaded file has a non-reproducible hash."""

    def __init__(self, file_name: str) -> None:
        super().__init__(f"Non-reproducible hash value for file: {file_name}.")


class FileAlreadyExistsError(PandarusRemoteError):
    """Raised when an uploaded file already exists on the server."""

    def __init__(self, file_name: str) -> None:
        super().__init__(f"File: {file_name} already exists.")


class IntersectionWithSelfError(PandarusRemoteError):
    """Raised when an intersection is attempted with the same file."""

    def __init__(self, file_hash: str) -> None:
        super().__init__(f"Cannot intersect file: {file_hash} with itself.")


class InvalidIntersectionFileTypesError(PandarusRemoteError):
    """Raised when an intersection is attempted with invalid types."""

    def __init__(
        self,
        file1_hash: str,
        file1_type: str,
        file2_hash: str,
        file2_type: str,
    ) -> None:
        super().__init__(
            f"""
            Cannot intersect file: {file1_hash} of type: {file1_type} with
            file: {file2_hash} of type: {file2_type}. Both files must be
            vector datasets.
        """
        )


class InvalidIntersectionGeometryTypeError(PandarusRemoteError):
    """Raised when an intersection is attempted with invalid geometry types."""

    def __init__(
        self,
        file1_hash: str,
        file1_type: str,
        file2_hash: str,
        file2_type: str,
    ) -> None:
        super().__init__(
            f"""
            Cannot intersect file: {file1_hash} of type: {file1_type} with
            file: {file2_hash} of type: {file2_type}. Second file must be
            polygon/ multipolygon datasets.
        """
        )


class InvalidRasterstatsFileTypesError(PandarusRemoteError):
    """Raised when an rasterstats is attempted with invalid types."""

    def __init__(
        self,
        vector_hash: str,
        vector_type: str,
        raster_hash: str,
        raster_type: str,
    ) -> None:
        super().__init__(
            f"""
            Can't calculate raster_stats for file: {vector_hash} of type: {vector_type}
            ith file: {raster_hash} of type: {raster_type}. First file must be vector
            dataset and second file must be raster dataset.
        """
        )
