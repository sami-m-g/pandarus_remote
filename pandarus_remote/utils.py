# -*- coding: utf-8 -*-
import fiona
import hashlib
import rasterio


def sha256(filepath, blocksize=65536):
    """Generate SHA 256 hash for file at `filepath`"""
    hasher = hashlib.sha256()
    fo = open(filepath, 'rb')
    buf = fo.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fo.read(blocksize)
    return hasher.hexdigest()


def check_type(filepath):
    """Determine if a GIS dataset is raster or vector.

    ``filepath`` is a filepath of a GIS dataset file.

    Returns one of ``('vector', 'raster', None)``."""
    try:
        with fiona.open(filepath) as ds:
            assert ds.meta['schema']['geometry'] != 'None'
        return 'vector'
    except:
        try:
            with rasterio.open(filepath) as ds:
                assert ds.meta
            return 'raster'
        except:
            return None
