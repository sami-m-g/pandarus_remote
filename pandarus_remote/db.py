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

database = RetryDatabase(os.path.join(data_dir, "pandarus-remote.db"))


class File(Model):
    filepath = TextField()
    name = TextField()
    sha256 = TextField(unique=True)
    band = IntegerField(null=True)
    layer = TextField(null=True)
    field = TextField(null=True)
    kind = TextField()

    class Meta:
        database = database


class Intersection(Model):
    first = ForeignKeyField(File, related_name='first_fk')
    second = ForeignKeyField(File, related_name='second_fk')
    output_fp = TextField()

    class Meta:
        database = database


database.create_tables([File, Intersection], safe=True)
