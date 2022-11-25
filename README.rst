cjio, or CityJSON/io
====================

|License: MIT| |image1|

Python CLI to process and manipulate `CityJSON <http://www.cityjson.org>`_ files. 
The different operators can be chained to perform several processing operations in one step, the
CityJSON model goes through them and different versions of the CityJSON model can be saved as files along the pipeline.

Documentation
-------------

`cjio.readthedocs.io <https://cjio.readthedocs.io>`_

Installation
------------

It uses Python 3.6+ only.

To install the latest release:

.. code:: console

    pip install cjio

.. note:: The commands ``export``, ``triangulate``, ``reproject``, and ``validate`` require extra packages that are not install by default. You can install these packages by specifying the
    commands for pip.

    .. code:: console

        pip install 'cjio[export,reproject,validate]'

To install the development branch, and still develop with it:

.. code:: console

    git checkout develop
    virtualenv venv
    . venv/bin/activate
    pip install --editable '.[develop]'

**Note for Windows users**

If your installation fails based on a *pyproj* or *pyrsistent* error there is a small hack to get around it. 
Based on the python version you have installed you can download a wheel (binary of a python package) of the problem package/s. 
A good website to use is `here <https://www.lfd.uci.edu/~gohlke/pythonlibs>`_. 
You then run:

.. code:: console

    pip install [name of wheel file]

You can then continue with:

.. code:: console

    pip install cjio


Supported CityJSON versions
---------------------------

The operators (``cjio --version``) expect that your file is using the latest version `CityJSON schema <https://www.cityjson.org/specs/overview/>`_.
If your file uses an earlier version, you can upgrade it with the ``upgrade`` operator: ``cjio old.json upgrade save newfile.city.json``


Usage of the CLI
----------------

After installation, you have a small program called ``cjio``, to see its
possibilities:

.. code:: console

    cjio --help

    Commands:
      attribute_remove  Remove an attribute.
      attribute_rename  Rename an attribute.
      crs_assign        Assign a (new) CRS (an EPSG).
      crs_reproject     Reproject to a new EPSG.
      crs_translate     Translate the coordinates.
      export            Export to another format.
      info              Output information about the dataset.
      lod_filter        Filter only one LoD for a dataset.
      materials_remove  Remove all materials.
      merge             Merge the current CityJSON with other ones.
      metadata_create   Add the +metadata-extended properties.
      metadata_get      Shows the metadata and +metadata-extended of this...
      metadata_remove   Remove the +metadata-extended properties.
      metadata_update   Update the +metadata-extended.
      save              Save to a CityJSON file.
      subset            Create a subset, City Objects can be selected by: (1)...
      textures_locate   Output the location of the texture files.
      textures_remove   Remove all textures.
      textures_update   Update the location of the texture files.
      triangulate       Triangulate every surface.
      upgrade           Upgrade the CityJSON to the latest version.
      validate          Validate the CityJSON: (1) against its schemas (2)...
      vertices_clean    Remove duplicate vertices + orphan vertices

Or see the command-specific help by calling ``--help`` after a command:

.. code:: console

    cjio subset --help

    Usage: cjio subset [OPTIONS]

      Create a subset, City Objects can be selected by: (1) IDs of City Objects;
      (2) bbox; (3) City Object type; (4) randomly.

      These can be combined, except random which overwrites others.

      Option '--exclude' excludes the selected objects, or "reverse" the
      selection.

    Options:
      --id TEXT                       The ID of the City Objects; can be used
                                      multiple times.
      --bbox FLOAT...                 2D bbox: (minx miny maxx maxy).
      --random INTEGER                Number of random City Objects to select.
      --cotype [Building|Bridge|Road|TransportSquare|LandUse|Railway|TINRelief|WaterBody|PlantCover|SolitaryVegetationObject|CityFurniture|GenericCityObject|Tunnel]
                                      The City Object type
      --exclude                       Excludes the selection, thus delete the
                                      selected object(s).
      --help                          Show this message and exit.    


Pipelines of operators
----------------------

The input 3D city model opened is passed through all the operators, and it gets modified by some operators. 
Operators like ``info`` and ``validate`` output information in the console and just pass the 3D city model to the next operator.

.. code:: console

    cjio example.city.json subset --id house12 remove_materials save out.city.json
    cjio example.city.json remove_textures info
    cjio example.city.json upgrade validate save new.city.json
    cjio myfile.city.json merge '/home/elvis/temp/*.city.json' save all_merged.city.json


stdin and stdout
----------------

Starting from v0.8, cjio allows to read/write from stdin/stdout (standard input/output streams).

For reading, it accepts at this moment only `CityJSONL (text sequences with CityJSONFeatures) <https://www.cityjson.org/specs/#text-sequences-and-streaming-with-cityjsonfeature>`_.
Instead of putting the file name, ``stdin`` must be used.

For writing, both CityJSON files and `CityJSONL files <https://www.cityjson.org/specs/#text-sequences-and-streaming-with-cityjsonfeature>`_ can be piped to stdout.
Instead of putting the file name, ``stdout`` must be used.
Also, the different operators of cjio output messages/information, and those will get in the stdout stream, to avoid this add the flag ``--suppress_msg`` when reading the file, as shown below.

.. code:: console

    cat mystream.city.jsonl | cjio --suppress_msg stdin remove_materials save stdout 
    cjio --suppress_msg myfile.city.json remove_materials export jsonl stdout | less
    cat myfile.city.json | cjio --suppress_msg stdin crs_reproject 7415 export jsonl mystream.txt


Generating Binary glTF
----------------------

Convert the CityJSON ``example.city.json`` to a glb file
``/home/elvis/gltfs/example.glb``

.. code:: console

    cjio example.json export glb /home/elvis/gltfs

Convert the CityJSON ``example.city.json`` to a glb file
``/home/elvis/test.glb``

.. code:: console

    cjio example.city.json export glb /home/elvis/test.glb

Usage of the API
----------------

`cjio.readthedocs.io/en/stable/tutorials.html <https://cjio.readthedocs.io/en/stable/tutorials.html>`_

Docker
------

If docker is the tool of your choice, please read the following hints.

To run cjio via docker simply call:

.. code:: console

    docker run --rm  -v <local path where your files are>:/data tudelft3d/cjio:latest cjio --help


To give a simple example for the following lets assume you want to create a geojson which represents 
the bounding boxes of the files in your directory. Lets call this script *gridder.py*. It would look like this:

.. code:: python

    from cjio import cityjson
    import glob
    import ntpath
    import json
    import os
    from shapely.geometry import box, mapping

    def path_leaf(path):
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    files = glob.glob('./*.json')

    geo_json_dict = {
        "type": "FeatureCollection",
        "features": []
    }

    for f in files:
        cj_file = open(f, 'r')
        cm = cityjson.reader(file=cj_file)
        theinfo = json.loads(cm.get_info())
        las_polygon = box(theinfo['bbox'][0], theinfo['bbox'][1], theinfo['bbox'][3], theinfo['bbox'][4])
        feature = {
            'properties': {
                'name': path_leaf(f)
            },
            'geometry': mapping(las_polygon)
        }
        geo_json_dict["features"].append(feature)
        geo_json_dict["crs"] = {
            "type": "name",
            "properties": {
                "name": "EPSG:{}".format(theinfo['epsg'])
            }
        }
    geo_json_file = open(os.path.join('./', 'grid.json'), 'w+')
    geo_json_file.write(json.dumps(geo_json_dict, indent=2))
    geo_json_file.close()


This script will produce for all files with postfix ".json" in the directory a bbox polygon using 
cjio and save the complete geojson result in grid.json in place.

If you have a python script like this, simply put it inside your 
local data and call docker like this:

.. code:: console

    docker run --rm  -v <local path where your files are>:/data tudelft3d/cjio:latest python gridder.py

This will execute your script in the context of the python environment inside the docker image.


Example CityJSON datasets
-------------------------

There are a few `example files on the CityJSON webpage <https://www.cityjson.org/datasets/>`_.

Alternatively, any `CityGML <https://www.ogc.org/standards/citygml>`_ file can be
automatically converted to CityJSON with the open-source project
`citygml-tools <https://github.com/citygml4j/citygml-tools>`_ (based on
`citygml4j <https://github.com/citygml4j/citygml4j>`_).


Acknowledgements
----------------

The glTF exporter is adapted from Kavisha's
`CityJSON2glTF <https://github.com/tudelft3d/CityJSON2glTF>`_.

.. |License: MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://github.com/tudelft3d/cjio/blob/master/LICENSE
.. |image1| image:: https://badge.fury.io/py/cjio.svg
   :target: https://pypi.org/project/cjio/
