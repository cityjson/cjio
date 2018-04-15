import click
import json
import sys

import info

# https://stackoverflow.com/questions/47437472/in-python-click-how-do-i-see-help-for-subcommands-whose-parents-have-required

# info
# convert2obj
# validate
# conver2gltf
# save
# compress
# decompress
# merge [list-files]
# subset
# remove_textures
# remove_materials
# update_bbox
# remove_duplicate_vertices
# remove_orphan_vertices


# @click.group(chain=True, invoke_without_command=True)
@click.group(chain=True)
@click.argument('input', type=click.File('r'))
def cli(input):
    """Processes a CityJSON and allows different outputs.
    The operators can be chained to perform several processing
    in one step. One commands feeds into the next.

    Example:

    \b
        cjio example.json compress --digit 3 info
        cjio example.json remove_textures subset 100 100 400 400 compress save out.json
    """
    pass


@cli.resultcallback()
def process_pipeline(processors, input):
    j = json.loads(input.read())
    for processor in processors:
        j = processor(j)
    # print "CRS: ", j["metadata"]["crs"]["epsg"]


@cli.command('info')
def info_cmd():
    """Outputs a JSON structured object with different information
    about the CityJSON file
    """
    def processor(j):
        info.print_info(j)
        return j
    return processor


@cli.command('save')
@click.argument('filename', type=click.Path())
@click.option('--indent', default=0)
def save_cmd(filename, indent):
    """Save the CityJSON file"""
    def processor(j):
        if indent == 0:
            json_str = json.dumps(j)
        else:
            json_str = json.dumps(j, indent=indent)
        f = open(filename, "w")
        f.write(json_str)
        return j
    return processor


@cli.command('update_bbox')
def info_cmd():
    def processor(j):
        j["metadata"]["crs"]["epsg"] = 999
        return j
    return processor




if __name__ == '__main__':
    cli()    