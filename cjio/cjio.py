
import click
import json
import sys
import copy
import glob

from cjio import cityjson



#-- https://stackoverflow.com/questions/47437472/in-python-click-how-do-i-see-help-for-subcommands-whose-parents-have-required
class PerCommandArgWantSubCmdHelp(click.Argument):
    def handle_parse_result(self, ctx, opts, args):
        # check to see if there is a --help on the command line
        if any(arg in ctx.help_option_names for arg in args):
            # if asking for help see if we are a subcommand name
            for arg in opts.values():
                if arg in ctx.command.commands:
                    # this matches a sub command name, and --help is
                    # present, let's assume the user wants help for the
                    # subcommand
                    args = [arg] + args
        return super(PerCommandArgWantSubCmdHelp, self).handle_parse_result(
            ctx, opts, args)


@click.group(chain=True)
@click.version_option(version='0.2.1')
@click.argument('input', cls=PerCommandArgWantSubCmdHelp)
@click.option('--ignore_duplicate_keys', is_flag=True, help='Load a CityJSON file even if some City Objects have the same keys')
@click.pass_context
def cli(context, input, ignore_duplicate_keys):
    """Process and manipulate a CityJSON file, and allow
    different outputs. The different operators can be chained
    to perform several processing in one step, the CityJSON model
    goes through the different operators.

    To get help on specific command, eg for 'validate':

    \b
        cjio validate --help

    Usage examples:

    \b
        cjio example.json validate
        cjio example.json remove_textures info
        cjio example.json subset --id house12 remove_materials save out.json
    """
    context.obj = {"argument": input}


@cli.resultcallback()
@click.pass_context
def process_pipeline(context, processors, input, ignore_duplicate_keys):
    try:
        f = click.open_file(input, mode='r')
        cm = cityjson.reader(f, ignore_duplicate_keys=ignore_duplicate_keys)
    except ValueError as e:
        # click.echo(context.get_usage() + "\n")
        raise click.ClickException('%s: "%s".' % (e, input))
    except IOError as e:
        # click.echo(context.get_usage() + "\n")
        raise click.ClickException('Invalid file: "%s".' % (input))
    for processor in processors:
        cm = processor(cm)


@cli.command('info')
@click.pass_context
def info_cmd(context):
    """Output info in simple JSON."""
    def processor(cm):
        theinfo = cm.get_info()
        click.echo(theinfo)
        return cm
    return processor


@cli.command('save')
@click.argument('filename', type=click.File('w'))
@click.option('--indent', default=0)
def save_cmd(filename, indent):
    """Save the CityJSON to a file."""
    def processor(cm):
        if indent == 0:
            json_str = json.dumps(cm.j, separators=(',',':'))
        else:
            json_str = json.dumps(cm.j, indent=indent)
        filename.write(json_str)
        return cm
    return processor


@cli.command('update_bbox')
def update_bbox_cmd():
    """
    Update the bbox of a CityJSON file.
    If there is none then it is added.
    """
    def processor(cm):
        cm.update_bbox()
        return cm
    return processor


@cli.command('validate')
@click.option('--hide_errors', is_flag=True, help='Do not print all the errors.')
@click.option('--skip_schema', is_flag=True, help='Skip the schema validation (since it can be painfully slow).')
def validate_cmd(hide_errors, skip_schema):
    """
    Validate the CityJSON file: (1) against its schema; (2) extra validations.
    """
    def processor(cm):
        bValid, woWarnings, errors, warnings = cm.validate(skip_schema=skip_schema)
        click.echo('===== Validation =====')
        if bValid == True:
            click.echo(click.style('File is valid', fg='green'))
        else:    
            click.echo(click.style('File is invalid', fg='red'))
        if woWarnings == False:
            click.echo(click.style('File has warnings', fg='red'))
        if not hide_errors and bValid is False:
            click.echo("--- ERRORS ---")
            click.echo(errors)
        if not hide_errors and woWarnings is False:
            click.echo("--- WARNINGS ---")
            click.echo(warnings)
        click.echo('======================')
        return cm
    return processor


@cli.command('merge')
@click.argument('filepattern')
def merge_cmd(filepattern):
    """
    Merge the current CityJSON with others.
    All City Objects with their textures/materials/templates are handled.
    
    Possible to give a wildcard but put it between quotes:

        $ cjio myfile.json merge '/home/elvis/temp/*.json' info
    """
    def processor(cm):
        lsCMs = []
        g = glob.glob(filepattern)
        for i in g:
            try:
                f = click.open_file(i, mode='r')
                lsCMs.append(cityjson.reader(f))
            except ValueError as e:
                click.echo('shit')
                raise click.ClickException('%s: "%s".' % (e, input))
            except IOError as e:
                click.echo('shit')
                raise click.ClickException('Invalid file: "%s".' % (input))
        if len(lsCMs) == 0:
            click.echo("WARNING: No files to merge.")
        else:
            # for i in lsCMs:
                # click.echo(i)
            cm.merge(lsCMs)
        return cm
    return processor


@cli.command('subset')
@click.option('--id', multiple=True, help='The ID of the CityObjects; can be used multiple times.')
@click.option('--bbox', nargs=4, type=float, help='2D bbox: minx miny maxx maxy')
@click.option('--cotype',
    type=click.Choice(['Building', 'Bridge', 'Road', 'TransportSquare', 'LandUse', 'Railway', 'TINRelief', 'WaterBody', 'PlantCover', 'SolitaryVegetationObject', 'CityFurniture', 'GenericCityObject', 'Tunnel']), 
    help='The City Object type')
def subset_cmd(id, bbox, cotype):
    """
    Create a subset of a CityJSON file.
    One can select City Objects by 
    (1) IDs;
    (2) bbox;
    (3) CityObject type.
    """
    def processor(cm):
        s = copy.deepcopy(cm)
        if len(id) > 0:
            s = s.get_subset_ids(id)
        if len(bbox) > 0:
            s = s.get_subset_bbox(bbox)
        if cotype is not None:
            s = s.get_subset_cotype(cotype)
        return s 
    return processor


@cli.command('remove_duplicate_vertices')
def remove_duplicate_vertices_cmd():
    """
    Remove duplicate vertices a CityJSON file.
    Only the geometry vertices are processed,
    and not those of the textures/templates.
    """
    def processor(cm):
        cm.remove_duplicate_vertices()
        return cm
    return processor


@cli.command('remove_orphan_vertices')
def remove_orphan_vertices_cmd():
    """
    Remove orphan vertices a CityJSON file.
    Only the geometry vertices are processed,
    and not those of the textures/templates.
    """
    def processor(cm):
        cm.remove_orphan_vertices()
        return cm
    return processor


@cli.command('remove_materials')
def remove_materials_cmd():
    """
    Remove all materials from a CityJSON file.
    """
    def processor(cm):
        cm.remove_materials()
        return cm
    return processor


@cli.command('decompress')
def decompress_cmd():
    """
    Decompress a CityJSON file, ie remove the "tranform".
    """
    def processor(cm):
        if (cm.decompress() == False):
            click.echo("WARNING: File is not compressed.")
        return cm
    return processor


@cli.command('remove_textures')
def remove_textures_cmd():
    """
    Remove all textures from a CityJSON file.
    """
    def processor(cm):
        cm.remove_textures()
        return cm
    return processor


@cli.command('update_crs')
@click.argument('newcrs', type=int)
def update_crs_cmd(newcrs):
    """
    Update the CRS with a new value.
    Can be used to assign one to a file that doesn't have any.
    """
    def processor(cm):
        cm.set_crs(newcrs)
        return cm
    return processor


