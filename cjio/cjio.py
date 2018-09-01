import os.path
from os import makedirs

import click
import json
import sys
import copy
import glob
import cjio
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
@click.version_option(version=cjio.__version__)
@click.argument('input', cls=PerCommandArgWantSubCmdHelp)
@click.option('--ignore_duplicate_keys', is_flag=True, help='Load a CityJSON file even if some City Objects have the same IDs (technically invalid file)')
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
    extensions = ['.json', '.off', '.poly'] #-- input allowed
    try:
        f = click.open_file(input, mode='r')
        extension = os.path.splitext(input)[1].lower()
        if extension not in extensions:
            raise IOError("File type not supported (only .json, .off, and .poly).")
        #-- OFF file
        if (extension == '.off'):
            cm = cityjson.off2cj(f)
        #-- POLY file
        elif (extension == '.poly'):
            cm = cityjson.poly2cj(f)            
        #-- CityJSON file
        else: 
            cm = cityjson.reader(file=f, ignore_duplicate_keys=ignore_duplicate_keys)
    except ValueError as e:
        # click.echo(context.get_usage() + "\n")
        raise click.ClickException('%s: "%s".' % (e, input))
    except IOError as e:
        # click.echo(context.get_usage() + "\n")
        raise click.ClickException('Invalid file: "%s".\n%s' % (input, e))
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


@cli.command('export')
@click.argument('filename')
def export_cmd(filename):
    """Export the CityJSON to an OBJ file.
    
    Textures are not supported, sorry.
    """
    def processor(cm):
        #-- output allowed
        extensions = ['.obj'] 
        f = os.path.basename(filename)
        d = os.path.abspath(os.path.dirname(filename))
        if not os.path.isdir(d):
            os.makedirs(d)
        p = os.path.join(d, f)
        try:
            extension = os.path.splitext(p)[1].lower()
            if (extension not in extensions):
                raise IOError("Only .obj files supported")
            fo = click.open_file(p, mode='w')
            click.echo("Exporting to OBJ")
            re = cm.export2obj()
            fo.write(re.getvalue())
            # fo.close()
        except IOError as e:
            raise click.ClickException('Invalid output file: "%s".\n%s' % (p, e))                
        except ModuleNotFoundError as e:
            str = "OBJ export skipped: Python module 'mapbox_earcut' missing (to triangulate faces)"
            click.echo(click.style(str, fg='red'))
            str = "Install it: https://github.com/skogler/mapbox_earcut_python"
            click.echo(str)
        return cm
    return processor


@cli.command('save')
@click.argument('filename')
@click.option('--indent', default=0)
@click.option('--textures', default=None, 
              type=str,
              help='Path to the new textures directory. This command copies the textures to a new location. Useful when creating an independent subset of a CityJSON file.')
def save_cmd(filename, indent, textures):
    """Save the CityJSON to a file."""
    def processor(cm):
        f = os.path.basename(filename)
        d = os.path.abspath(os.path.dirname(filename))
        if not os.path.isdir(d):
            os.makedirs(d)
        p = os.path.join(d, f)
        try:
            fo = click.open_file(p, mode='w')
            if textures:
                cm.copy_textures(textures, p)
            if indent == 0:
                json_str = json.dumps(cm.j, separators=(',',':'))
                fo.write(json_str)
            else:
                json_str = json.dumps(cm.j, indent=indent)
                fo.write(json_str)
        except IOError as e:
            raise click.ClickException('Invalid output file: "%s".\n%s' % (p, e))                
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
@click.option('--extensions', is_flag=True, help='Validate the extensions in the file (schemas needed).')
@click.option('--folder_schemas', help='Specify a folder where the schemas are (cityjson.json needs to be the master file).')
def validate_cmd(hide_errors, skip_schema, folder_schemas, extensions):
    """
    Validate the CityJSON file: (1) against its schemas; (2) extra validations.
    Only files with version >0.6 can be validated.

    The schemas are fetched automatically, based on the version of the file.
    Although one can specify schemas with the '--folder_schemas' option.
    
    If the file is too large (and thus validation is slow),
    an option is to crop a subset and just validate it:

        cjio myfile.json subset --random 2 validate
    """
    def processor(cm):
        if folder_schemas is not None:
            if os.path.exists(folder_schemas) == False:
                click.echo(click.style("Folder for schemas unknown. Validation aborted.", fg='red'))
                return cm
            else:
                click.echo('===== Validation (schemas: %s) =====' % (folder_schemas)) 
        else:
            click.echo('===== Validation (schemas v%s) =====' % (cm.j['version']))
        #-- validate    
        bValid, woWarnings, errors, warnings = cm.validate(skip_schema=skip_schema, folder_schemas=folder_schemas, with_extensions=extensions)
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
        click.echo('=====================================')
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
@click.option('--id', multiple=True, help='The ID of the City Objects; can be used multiple times.')
@click.option('--bbox', nargs=4, type=float, help='2D bbox: (minx miny maxx maxy).')
@click.option('--random', type=int, help='Number of random City Objects to select.')
@click.option('--cotype',
    type=click.Choice(['Building', 'Bridge', 'Road', 'TransportSquare', 'LandUse', 'Railway', 'TINRelief', 'WaterBody', 'PlantCover', 'SolitaryVegetationObject', 'CityFurniture', 'GenericCityObject', 'Tunnel']), 
    help='The City Object type')
@click.option('--invert', is_flag=True, help='Invert the selection, thus delete the selected object(s).')
def subset_cmd(id, bbox, random, cotype, invert):
    """
    Create a subset of a CityJSON file.
    One can select City Objects by
    (1) IDs of City Objects;
    (2) bbox;
    (3) City Object type;
    (4) randomly.

    These can be combined, except random which overwrites others.

    Option '--invert' inverts the selection, thus delete the selected object(s).
    """
    def processor(cm):
        s = copy.deepcopy(cm)
        if random is not None:
            s = s.get_subset_random(random, invert=invert)
            return s
        if len(id) > 0:
            s = s.get_subset_ids(id, invert=invert)
        if len(bbox) > 0:
            s = s.get_subset_bbox(bbox, invert=invert)
        if cotype is not None:
            s = s.get_subset_cotype(cotype, invert=invert)
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


@cli.command('compress')
@click.option('--digit', default=3, type=click.IntRange(1, 10), help='Number of digit to keep.')
def compress_cmd(digit):
    """
    Compress a CityJSON file, ie stores its vertices with integers.
    """
    def processor(cm):
        try:
            cm.compress(digit)
        except Exception as e:
            click.echo("WARNING: %s." % e)
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


@cli.command('update_epsg')
@click.argument('newepsg', type=int)
def update_crs_cmd(newepsg):
    """
    Update the CRS with a new value (give only the EPSG).
    Can be used to assign one to a file that doesn't have any.
    """
    def processor(cm):
        cm.set_epsg(newepsg)
        return cm
    return processor


@cli.command('reproject')
@click.argument('epsg', type=int)
def update_crs_cmd(epsg):
    """
    Reproject the CityJSON to a new EPSG.
    The current file must have an EPSG defined (do it with function update_epsg()).
    """
    def processor(cm):
        if (cm.get_epsg() == None):
            click.echo("WARNING: CityJSON has no EPSG defined, can't be reprojected.")
        else:    
            cm.reproject(epsg)
        return cm
    return processor


@cli.command('upgrade_version')
@click.argument('newversion')
def upgrade_version_cmd(newversion):
    """
    Upgrade the CityJSON to a new version.
    It takes care of *everything* (touch wood).

        $ cjio myfile.json upgrade_version 0.7 
    """
    def processor(cm):
        if (cm.upgrade_version(newversion) == False):
            click.echo("WARNING: File cannot be upgraded to this version.")
        return cm
    return processor


@cli.command('locate_textures')
def locate_textures_cmd():
    """
    Output the location of the texture files.
    """
    def processor(cm):
        loc = cm.get_textures_location()
        click.echo(loc)
        return cm
    return processor


@cli.command('update_textures')
@click.argument('newlocation', type=str)
@click.option('--relative', is_flag=True, help='Convert texture file paths to relative paths.')
def update_textures_cmd(newlocation, relative):
    """
    Update the location of the texture files.
    Can be used if the texture files were moved to new directory.
    """
    def processor(cm):
        cm.update_textures_location(newlocation, relative=relative)
        return cm
    return processor
