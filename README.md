# cjio, or CityJSON/io

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![](https://badge.fury.io/py/cjio.svg)

Python CLI to process and manipulate [CityJSON](http://www.cityjson.org) files.
The different operators can be chained to perform several processing in one step, the CityJSON model goes through them and allows to save to a new CityJSON at the end.

It uses Python 3.3+ only.

To install and still develop with it:

```console
$ virtualenv venv
$ . venv/bin/activate
$ pip3 install --editable .
```

Then you have a small program called `cjio`, to see its possibities:
```console
$ cjio --help

  decompress                 Decompress a CityJSON file, ie remove the...
  info                       Output info in simple JSON.
  merge                      Merge the current CityJSON with others.
  remove_duplicate_vertices  Remove duplicate vertices a CityJSON file.
  remove_materials           Remove all materials from a CityJSON file.
  remove_orphan_vertices     Remove orphan vertices a CityJSON file.
  remove_textures            Remove all textures from a CityJSON file.
  save                       Save the CityJSON to a file.
  subset                     Create a subset of a CityJSON file.
  update_bbox                Update the bbox of a CityJSON file.
  update_crs                 Update the CRS with a new value.
  validate                   Validate the CityJSON file: (1) against its...
```


## Pipelines of operators

The 3D city model opened is passed through all the operators, and it gets modified by some operators.
Operators like `nfo` and `validate` output information in the console and just pass the 3D city model to the next operator.

```console
$ cjio example.json validate
$ cjio example.json remove_textures info
$ cjio example.json subset --id house12 info remove_materials info save out.json
```


## Where can I get data to test it?

There are a few [example files on the CityJSON webpage](http://www.cityjson.org/en/0.6/datasets/).

Alternatively, any [CityGML](https://www.citygml.org) file can be automatically converted to CityJSON with the open-source project [citygml4j](https://github.com/citygml4j/citygml4j).


