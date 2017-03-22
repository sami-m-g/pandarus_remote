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
* `redis <https://pypi.python.org/pypi/redis>`__
* `rasterio <https://github.com/mapbox/rasterio>`__
* `requests <http://docs.python-requests.org/en/master/>`__
* `rq <http://python-rq.org/>`__

In addition, ``pandarus_remote`` requires that `Redis <https://redis.io/>`__ be installed.

Running the web service
=======================

A Redis server must be running on the local machine.

A worker process for ``rq`` should be started with the command ``rq worker``.

Finally, run the ``flask`` application any way you want. For example, to run the test server (not in production!), do:

.. code-block:: bash

    export FLASK_APP=/path/to/pandarus_remote/__init__.py
    flask run

Environment variables
---------------------

The following environment variables can be used to configure ``pandarus_remote``:

* ``PANDARUS_EXPORT_FORMAT``: A string specifying the Fiona driver to use, like "GPKG" or "GeoJSON"
* ``PANDARUS_CPUS``: The number of CPUs to use when performing intersection calculations

API endpoints
=============

The following API endpoints are supported:

/
-

Ping the server. Returns something like ``pandarus_remote web service, version (1, 0)``.

HTTP method: **GET**

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
            ('file name', 'hex-encoded sha256 hash of file contents', 'type of file')
        ],
        'intersections': [
            ('input file 1 sha256 hash', 'input file 2 sha256 hash')
        ],
        'remaining': [
            ('input file 1 sha256 hash', 'input file 2 sha256 hash')
        ],
        'rasterstats': [
            ('vector file sha256 hash', 'raster file sha256 hash')
        ]
    ]

/upload
-------

Upload a spatial data file. The provided file must be openable by `fiona <https://github.com/Toblerity/Fiona>`__ or `rasterio <https://github.com/mapbox/rasterio>`__.

HTTP method: **POST**

Parameters
``````````

Post the following required form data:

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
* 406: The input data was invalid (either the hash wasn't correct or the file isn't a readable geospatial dataset)
* 409: File already exists
* 413: The uploaded file was too large (current limit is 250 MB)

/intersection
-------------

Request the download of a pandarus intersections JSON data file for two spatial datasets. Both spatial datasets should already be on the server (see ``/upload``), and the intersection should already be calculated (see ``/calculate-intersection``).

HTTP method: **POST**

Parameters
``````````

Post the following form data:

* ``first``: SHA 256 hash of first input file
* ``second``: SHA 256 hash of second input file

Responses
`````````

* 200: The requested file will be returned
* 400: The request form was missing a required field
* 404: An intersections file for this combination was not found

/intersection-file
------------------

Request the download of the new geospatial vector file created when calculating the intersection of two spatial datasets. Both spatial datasets should already be on the server (see ``/upload``), and the intersection should already be calculated (see ``/calculate-intersection``).

HTTP method: **POST**

Parameters
``````````

Post the following form data:

* ``first``: SHA 256 hash of first input file
* ``second``: SHA 256 hash of second input file

Responses
`````````

* 200: The requested file will be returned
* 400: The request form was missing a required field
* 404: An intersections file for this combination was not found

/calculate-intersection
-----------------------

Calculate a pandarus intersections file for two vector spatial datasets. Both spatial datasets should already be on the server (see ``/upload``). The second vector dataset must have the geometry type ``Polygon`` or ``MultiPolygon``.

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
* 406: Error in the files: Either the hashes were identical, or the files weren't vector datasets, or the second file didn't have the correct geometry type.
* 409: The requested intersection file already exists

/remaining
----------

Request the download of the JSON data file from a remaining areas calculation. Both spatial datasets should already be on the server (see ``/upload``), and the remaining areas should already be calculated (see ``/calculate-remaining``).

HTTP method: **POST**

Parameters
``````````

Post the following form data:

* ``first``: SHA 256 hash of first input file
* ``second``: SHA 256 hash of second input file

Responses
`````````

* 200: The requested file will be returned
* 400: The request form was missing a required field
* 404: An remaining areas file for this combination was not found

/calculate-remaining
--------------------

Calculate a pandarus remaining areas file for two vector spatial datasets. See the Pandarus documentation for more details on remaining areas. Both spatial datasets should already be on the server (see ``/upload``), and their intersection should already be calculated.

HTTP method: **POST**

Parameters
``````````
Post the following form data:

* ``first``: SHA 256 hash of first input file
* ``second``: SHA 256 hash of second input file

Responses
`````````

* 200: The requested remaining areas file will be calculated. Returns the URL of the job status resource (see `/status`) which can be polled to see when the calculation is finished.
* 400: The request form was missing a required field
* 404: One of the files or the calculated intersection result were not found
* 409: The requested remaining areas file already exists

/rasterstats
------------

Request the download of the JSON data file from a raster stats calculation. Both spatial datasets should already be on the server (see ``/upload``), and the raster stats should already be calculated (see ``/calculate-rasterstats``).

HTTP method: **POST**

Parameters
``````````

Post the following form data:

* ``vector``: SHA 256 hash of vector input file
* ``raster``: SHA 256 hash of raster input file

Responses
`````````

* 200: The requested file will be returned
* 400: The request form was missing a required field
* 404: An raster stats file for this combination was not found

/calculate-rasterstats
----------------------

Calculate a pandarus raster stats file for two vector spatial datasets. See the Pandarus documentation for more details on raster stats. Both spatial datasets should already be on the server (see ``/upload``), and their intersection should already be calculated.

HTTP method: **POST**

Parameters
``````````
Post the following form data:

* ``vector``: SHA 256 hash of vector input file
* ``raster``: SHA 256 hash of raster input file

Responses
`````````

* 200: The requested raster stats file will be calculated. Returns the URL of the job status resource (see `/status`) which can be polled to see when the calculation is finished.
* 400: The request form was missing a required field
* 404: One of the files was not found
* 406: One of the files had an incorrect data type
* 409: The requested remaining areas file already exists

/status/<job_id>
----------------

Get the status of a currently running job. Job status URLs are returned by the ``/calculate-intersection`` and ``/calculate-area`` endpoints.

HTTP method: **GET**

Reponse
```````

* 200: Returns a text response giving the current job status. If the job is finished, the response will be ``finished``.
* 404: The requested job id was not found
