
# jsio : a toolbox to manipulate 3D city models in CityJSON

import click
from functools import update_wrapper
import json

import info




@click.group(chain=True)
def cli():
    """cjio processes a bunch of CityJSON through pillow in a unix
    pipe.  One commands feeds into the next.

    Example:

    \b
        imagepipe open -i example01.jpg resize -w 128 display
        imagepipe open -i example02.jpg blur save
    """

@cli.resultcallback()
def process_commands(processors):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()
    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)
    # Evaluate the stream and throw away the items.
    for _ in stream:
        pass


def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """
    def new_func(*args, **kwargs):
        def processor(stream):
            return f(stream, *args, **kwargs)
        return processor
    return update_wrapper(new_func, f)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """
    @processor
    def new_func(stream, *args, **kwargs):
        for item in stream:
            yield item
        # yield stream
        for item in f(*args, **kwargs):
            yield item
    return update_wrapper(new_func, f)



@cli.command('save')
@click.argument('output_file', type=click.File('w'))
@processor
def save_cmd(j, output_file):
    """Saves all processed images to a series of files."""
    try:
        click.echo('Saving output to "%s"' % (output_file))
        yield "saved."
    except Exception as e:
        click.echo('Could not save CityJSON file "%s"' % (output_file), err=True)


@cli.command('info')
@processor
def info_cmd(j):
    """Print some useful information about the CityJSON file."""
    # j = json.loads(input_file.read())
    click.echo('Printing info')
    click.echo(j["metadata"])
    # info.print_info(j)
    yield j


@cli.command('open')
# @click.option('-i', '--input_file', type=click.File('r'), help='The CityJSON file to open')
@click.argument('input_file', type=click.Path())
@generator
def open_cmd(input_file):
    """Loads one or multiple images for processing.  The input parameter
    can be specified multiple times to load more than one image.
    """
    try:
        click.echo('Opening "%s"' % input_file)
        j = json.loads(open(input_file).read())
        # print j["metadata"]
        yield j
    except Exception as e:
        click.echo('Could not open file "%s": %s' % (input_file, e), err=True)

# @cli1.command('convert2obj')
# @click.argument('input_file',  type=click.File('r'))
# @click.argument('output_file', type=click.File('w'))
# def convert2obj_cmd(input_file, output_file):
#     """Convert to OBJ"""
#     click.echo("-->convert to OBJ")
#     j = json.loads(input_file.read())
#     j["metadata"]["epsg"] = 999
#     json_str = json.dumps(j, indent=2)
#     output_file.write(json_str)



#########################

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
# @click.option('-i', '--input_file', type=click.File('r'))
# def cli2(input_file):
#     pass

# @cli2.resultcallback()
# def process_pipeline(processors, input_file):
#     stream = ()
#     for processor in processors:
#         stream = processor(stream)
#     for each in stream:
#         click.echo(each)

# def processor(f):
#     """Helper decorator to rewrite a function so that it returns another
#     function from it.
#     """
#     def new_func(*args, **kwargs):
#         def processor(stream):
#             return f(stream, *args, **kwargs)
#         return processor
#     return update_wrapper(new_func, f)

# @cli2.command('compress')
# @processor
# def compress_cmd():
#     """Compress the file"""
#     click.echo("-->compress" + input_file)


# # @cli2.command()
# # @click.argument('input_file', type=click.File('r'))
# # def decompress(input_file):
# #     """Decompress the file"""
# #     click.echo("-->decompress")



# cli = click.CommandCollection(sources=[cli1, cli2])

if __name__ == '__main__':
    cli()