"""Models for the __pandarus_remote__ web service."""
# pylint: disable=too-few-public-methods``
from peewee import AutoField, ForeignKeyField, IntegerField, Model, TextField


class BaseModel(Model):
    """Base model for the database."""


class File(BaseModel):
    """Model for a file in the database."""

    id = AutoField(primary_key=True)
    name = TextField()
    kind = TextField()
    sha256 = TextField(unique=True)
    file_path = TextField()
    band = IntegerField(null=True)
    layer = TextField(null=True)
    field = TextField(null=True)
    geometry_type = TextField(null=True)


class Intersection(BaseModel):
    """Model for an intersection between two files."""

    id = AutoField(primary_key=True)
    first_file = ForeignKeyField(File, backref="first_file_fk")
    second_file = ForeignKeyField(File, backref="second_file_fk")
    data_file_path = TextField()
    vector_file_path = TextField()

    class Meta:
        """Meta class for the Intersection model."""

        indexes = [
            (("first_file", "second_file"), True),
        ]


class RasterStats(BaseModel):
    """Model for the statistics of a raster file."""

    id = AutoField(primary_key=True)
    vector_file = ForeignKeyField(File, backref="vector_file_fk")
    raster_file = ForeignKeyField(File, backref="raster_file_fk")
    output_file_path = TextField()

    class Meta:
        """Meta class for the RasterStats model."""

        indexes = [
            (("vector_file", "raster_file"), True),
        ]


class Remaining(BaseModel):
    """Model for the remaining area files."""

    id = AutoField(primary_key=True)
    intersection = ForeignKeyField(Intersection, backref="intersection_fk", unique=True)
    data_file_path = TextField()
