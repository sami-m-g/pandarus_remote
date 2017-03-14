# -*- coding: utf-8 -*-
from .filesystem import data_dir
from peewee import (
    BlobField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)
from playhouse.shortcuts import RetryOperationalError
import os


class RetryDatabase(RetryOperationalError, SqliteDatabase):
    pass

db_filepath = os.path.join(data_dir, "pandarus-remote.db")
print("Using database at", db_filepath)
database = RetryDatabase(db_filepath)


class File(Model):
    filepath = TextField()
    name = TextField()
    sha256 = TextField(unique=True)
    band = IntegerField(null=True)
    layer = TextField(null=True)
    field = TextField(null=True)
    kind = TextField()
    geometry_type = TextField(null=True)

    class Meta:
        database = database


class Intersection(Model):
    first = ForeignKeyField(File, related_name='first_fk')
    second = ForeignKeyField(File, related_name='second_fk')
    data_fp = TextField()
    vector_fp = TextField()

    class Meta:
        database = database
        indexes = [
            (('first', 'second'), True),
        ]


class RasterStats(Model):
    vector = ForeignKeyField(File, related_name='vector_fk')
    raster = ForeignKeyField(File, related_name='raster_fk')
    output = TextField()

    class Meta:
        database = database
        indexes = [
            (('vector', 'raster'), True),
        ]


class Remaining(Model):
    intersection = ForeignKeyField(Intersection, related_name='intersection_fk', unique=True)
    data_fp = TextField()

    class Meta:
        database = database


database.create_tables([File, Intersection, Remaining, RasterStats], safe=True)
