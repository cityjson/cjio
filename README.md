
# cjio, or CityJSON/io

Python CLI to process and manipulate [CityJSON](http://www.cityjson.org) files.
The different operators can be chained to perform several processing in one step, the CityJSON model goes through them and allows to save to a new CityJSON at the end.

It is only for uses Python 3.3+

To install and still develop with it:

```console
$ virtualenv venv
$ . venv/bin/activate
$ pip3 install -r requirements.txt --editable .
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


## Where can I get data to test it?

There are a few [example files on the CityJSON webpage](http://www.cityjson.org/en/0.6/datasets/).

Alternatively, any [CityGML](https://www.citygml.org) file can be automatically converted to CityJSON with the open-source project [citygml4j](https://github.com/citygml4j/citygml4j).


