import click
import json

import info


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



@click.group(chain=True, invoke_without_command=True)
@click.argument('input', type=click.File('r'))
def cli(input):
    pass

@cli.resultcallback()
def process_pipeline(processors, input):
    j = json.loads(input.read())
    for processor in processors:
        j = processor(j)
    print "CRS: ", j["metadata"]["crs"]["epsg"]


@cli.command('info')
def info_cmd():
    def processor(j):
        info.print_info(j)
        return j
    return processor





if __name__ == '__main__':
    cli()    