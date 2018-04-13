
import click
from functools import update_wrapper
import json

import info


# validate
# conver2gltf


@click.group()
def cli1():
    pass


@cli1.command('info')
@click.argument('input_file', type=click.File('r'))
def info_cmd(input_file):
    """Print some useful information about the CityJSON file."""
    j = json.loads(input_file.read())
    info.print_info(j)


@cli1.command('convert2obj')
@click.argument('input_file',  type=click.File('r'))
@click.argument('output_file', type=click.File('w'))
def convert2obj_cmd(input_file, output_file):
    """Convert to OBJ"""
    click.echo("-->convert to OBJ")
    j = json.loads(input_file.read())
    j["metadata"]["epsg"] = 999
    json_str = json.dumps(j, indent=2)
    output_file.write(json_str)



#########################

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

@click.group(chain=True, invoke_without_command=True)
@click.option('-i', '--input_file', type=click.File('r'))
def cli2(input_file):
    pass

@cli2.resultcallback()
def process_pipeline(processors, input_file):
    stream = ()
    for processor in processors:
        stream = processor(stream)
    for each in stream:
        click.echo(each)

def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """
    def new_func(*args, **kwargs):
        def processor(stream):
            return f(stream, *args, **kwargs)
        return processor
    return update_wrapper(new_func, f)

@cli2.command('compress')
@processor
def compress_cmd():
    """Compress the file"""
    click.echo("-->compress" + input_file)


# @cli2.command()
# @click.argument('input_file', type=click.File('r'))
# def decompress(input_file):
#     """Decompress the file"""
#     click.echo("-->decompress")



cli = click.CommandCollection(sources=[cli1, cli2])

if __name__ == '__main__':
    cli()