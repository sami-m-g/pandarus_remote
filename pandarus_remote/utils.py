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


def is_valid_spatial_dataset(filepath):
    with fiona.drivers():
        try:
            with fiona.open(filepath) as source:
                assert source.meta
                return True
        except:
            pass
    with rasterio.drivers():
        try:
            with rasterio.open(filepath) as source:
                assert source.meta
                return True
        except:
            pass
    return False
