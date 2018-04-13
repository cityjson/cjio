
import click
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
    cjinfo.print_info(j)


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


# compress
# decompress
# merge [list-files]
# subset
# remove_textures
# remove_materials
# update_bbox
# remove_duplicate_vertices
# remove_orphan_vertices

@click.group()
def cli2():
    pass

@cli2.command()
@click.argument('input_file', type=click.File('r'))
def compress(input_file):
    """Compress the file"""
    click.echo("-->compress")

@cli2.command()
@click.argument('input_file', type=click.File('r'))
def decompress(input_file):
    """Decompress the file"""
    click.echo("-->decompress")



cli = click.CommandCollection(sources=[cli1, cli2])

if __name__ == '__main__':
    cli()