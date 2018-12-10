# cjio, or CityJSON/io

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/tudelft3d/cjio/blob/master/LICENSE)
[![](https://badge.fury.io/py/cjio.svg)](https://pypi.org/project/cjio/)

Python CLI to process and manipulate [CityJSON](http://www.cityjson.org) files.
The different operators can be chained to perform several processing operations in one step, the CityJSON model goes through them and different versions of the CityJSON model can be saved as files along the pipeline.


## Installation

It uses Python 3.3+ only.

To install the latest release:

```console
pip3 install cjio
```

To install the development branch, and still develop with it:

```console
git checkout development
virtualenv venv
. venv/bin/activate
pip3 install --editable .
```

Alternatively, you can use the included Pipfile to manage the virtual environment with [pipenv](https://pipenv.readthedocs.io/en/latest/).

**Note for Windows users**

If your installation fails based on a *pyproj* error there is a small hack to get around it.
You can download a pyproj wheel (binary of a python package) based on the python version you have installed.
A good website to use is [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyproj).
You then run:

```console
pip3 install [name of wheel file]
```

You can then continue with:

```console
pip3 install cjio
```

## Usage

After installation, you have a small program called `cjio`, to see its possibities:

```console
cjio --help

Commands:
  assign_epsg                Assign a (new) EPSG.
  compress                   Compress a CityJSON file, ie stores its...
  decompress                 Decompress a CityJSON file, ie remove the...
  export                     Export the CityJSON to an OBJ file.
  info                       Output info in simple JSON.
  locate_textures            Output the location of the texture files.
  merge                      Merge the current CityJSON with others.
  remove_duplicate_vertices  Remove duplicate vertices a CityJSON file.
  remove_materials           Remove all materials from a CityJSON file.
  remove_orphan_vertices     Remove orphan vertices a CityJSON file.
  remove_textures            Remove all textures from a CityJSON file.
  reproject                  Reproject the CityJSON to a new EPSG.
  save                       Save the CityJSON to a file.
  subset                     Create a subset of a CityJSON file.
  update_bbox                Update the bbox of a CityJSON file.
  update_textures            Update the location of the texture files.
  upgrade_version            Upgrade the CityJSON to the latest version.
  validate                   Validate the CityJSON file: (1) against its...  
```


## Pipelines of operators

The 3D city model opened is passed through all the operators, and it gets modified by some operators.
Operators like `info` and `validate` output information in the console and just pass the 3D city model to the next operator.

```console
$ cjio example.json subset --id house12 info remove_materials info save out.json
$ cjio example.json remove_textures compress info
$ cjio example.json upgrade_version save new.json
$ cjio myfile.json merge '/home/elvis/temp/*.json' save all_merged.json
```


## Validation of CityJSON files against the schema

To validate a CityJSON file against the [schemas of CityJSON](https://github.com/tudelft3d/cityjson/tree/master/schema) (this will automatically fetch the schemas for the version of CityJSON):

```console
$ cjio myfile.json validate
```

If the file is too large (and thus validation is slow), an option is to crop a subset and just validate it:

```console
$ cjio myfile.json subset --random 2 validate
```

If you want to use your own schemas, give the folder where the master schema file `cityjson.json` is located:

```console
$ cjio example.json validate --folder_schemas /home/elvis/temp/myschemas/
```

## Example CityJSON datasets

There are a few [example files on the CityJSON webpage](https://www.cityjson.org/en/0.8/datasets/).

Alternatively, any [CityGML](https://www.citygml.org) file can be automatically converted to CityJSON with the open-source project [citygml4j](https://github.com/citygml4j/citygml4j).


