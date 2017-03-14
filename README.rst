===============
Pandarus_remote
===============

Pandarus_remote is a web service for processing and managing data for regionalized life cycle assessment using `pandarus <https://pypi.python.org/pypi/pandarus>`__. It is meant to be used by the `brightway2-regional <https://brightway2-regional.readthedocs.io/>`__ library.

.. contents::

Installation
============

``pandarus_remote`` can be installed using pip, but your life will be much easier if you use ``conda`` to get consistent dependencies:

.. code-block:: bash

    conda config --add channels conda-forge cmutel
    conda create -n pandarus python=3.5
    source activate pandarus
    conda install pandarus_remote

Requirements
------------

``pandarus_remote`` requires the following Python libraries:

* `appdirs <https://pypi.python.org/pypi/appdirs>`__
* `docopt <https://pypi.python.org/pypi/docopt>`__
* `fiona <https://pypi.python.org/pypi/Fiona>`__
* `flask <http://flask.pocoo.org/>`__
* `pandarus <https://pypi.python.org/pypi/pandarus>`__
* `peewee <http://docs.peewee-orm.com/en/latest/>`__
* `rasterio <https://github.com/mapbox/rasterio>`__
* `requests <http://docs.python-requests.org/en/master/>`__
* `rq <http://python-rq.org/>`__

Running the web service
=======================

A Redis server must be running on the local machine.

A worker process for ``rq`` should be started with the command ``rq worker``.

Finally, run the ``flask`` application any way you want.

API endpoints
=============

The following API endpoints are supported:

/catalog
--------

Get the list of spatial datasets and results currently available on the server.

HTTP method: **GET**

Response
````````

* 200: Return a JSON payload of the form:

.. code-block:: javascript

    [
        'files': [
            ('file name', 'hex-encoded sha256 hash of file contents')
        ],
        'intersections': [
            ('input file name 1', 'input file name 2', 'intersections output file name')
        ],
        'areas': [
            ('input file name', 'areas output file name')
        ]
    ]

/upload
-------

Upload a spatial data file. The provided file must be openable by `fiona <https://github.com/Toblerity/Fiona>`__ or `rasterio <https://github.com/mapbox/rasterio>`__.

HTTP method: **POST**

Parameters
``````````

Post the following form data:

* ``name``: File name
* ``sha256``: SHA 256 hash of file
* ``band``: Raster band number. This field is required; pass ``''`` if single-band raster or vector dataset.
* ``layer``: Vector layer name. This field is required; pass ``''`` if single-layer vector or raster dataset.
* ``field``: Vector field that uniquely identifies spatial features. This field is required; pass ``''`` if raster dataset.

The file should be in the field ``file``.

Responses
`````````

* 201: The file was uploaded and registered. Returns a JSON payload:

.. code-block:: javascript

    {
        'filename': 'some file name',
        'sha256': 'hex-encoded sha256 hash of file contents'
    }

* 400: The request form was missing a required field
* 406: The input data was invalid
* 409: File already exists
* 413: The uploaded file was too large (current limit is 250 MB)

/intersection
-------------

Request the download of a pandarus intersections file for two spatial datasets. Both spatial datasets should already be on the server (see ``/upload``), and the intersection should already be calculated (see ``/calculate-intersection``).

HTTP method: **POST**

Parameters
``````````

Post the following form data:

* ``first``: SHA 256 hash of first input file
* ``second``: SHA 256 hash of second input file

Responses
`````````

* 200: The requested intersections file will be returned
* 400: The request form was missing a required field
* 404: An intersections file for this combination was not found
* 406: Invalid request

/calculate-intersection
-----------------------

Calculate a pandarus intersections file for two spatial datasets. Both spatial datasets should already be on the server (see ``/upload``).

HTTP method: **POST**

Parameters
``````````

Post the following form data:

* ``first``: SHA 256 hash of first input file
* ``second``: SHA 256 hash of second input file

Responses
`````````

* 200: The requested intersections file will be calculated. Returns the URL of the job status resource (see `/status`) which can be polled to see when the calculation is finished.
* 400: The request form was missing a required field
* 404: One of the files were not found
* 406: The two provided file hashes were identical
* 409: The requested intersection file already exists

/status/<job_id>
----------------

Get the status of a currently running job. Job status URLs are returned by the ``/calculate-intersection`` and ``/calculate-area`` endpoints.

HTTP method: **GET**

Reponse
```````

* 200: Returns a text response giving the current job status. If the job is finished, the response will be ``finished``.
