
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


def print_cmd_status(s):
    click.echo(click.style(s, bg='cyan', fg='black'))


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
        cjio example.json info validate
        cjio example.json assign_epsg 7145 remove_textures export output.obj
        cjio example.json subset --id house12 save out.json
    """
    context.obj = {"argument": input}


@cli.resultcallback()
def process_pipeline(processors, input, ignore_duplicate_keys):
    extensions = ['.json', '.off', '.poly'] #-- input allowed
    try:
        f = click.open_file(input, mode='r')
        extension = os.path.splitext(input)[1].lower()
        if extension not in extensions:
            raise IOError("File type not supported (only .json, .off, and .poly).")
        #-- OFF file
        if (extension == '.off'):
            print_cmd_status("Converting %s to CityJSON" % (input))
            cm = cityjson.off2cj(f)
        #-- POLY file
        elif (extension == '.poly'):
            print_cmd_status("Converting %s to CityJSON" % (input))
            cm = cityjson.poly2cj(f)            
        #-- CityJSON file
        else: 
            print_cmd_status("Parsing %s" % (input))
            cm = cityjson.reader(file=f, ignore_duplicate_keys=ignore_duplicate_keys)
            if (cm.get_version() not in cityjson.CITYJSON_VERSIONS_SUPPORTED):
                allv = ""
                for v in cityjson.CITYJSON_VERSIONS_SUPPORTED:
                    allv = allv + v + "/"
                str = "CityJSON version %s not supported (only versions: %s), not every operators will work." % (cm.get_version(), allv)
                raise click.ClickException(str)
            elif (cm.get_version() != cityjson.CITYJSON_VERSIONS_SUPPORTED[-1]):
                str = "v%s is not the latest version, and not everything will work.\n" % cm.get_version()
                str += "Upgrade the file with 'upgrade_version' command: 'cjio input.json upgrade_version save out.json'" 
                click.echo(click.style(str, fg='red'))
            
    except ValueError as e:
        raise click.ClickException('%s: "%s".' % (e, input))
    except IOError as e:
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
    """Export the CityJSON to another format.

    Currently only OBJ file are supported; textures are not supported, sorry.
    """
    def processor(cm):
        #-- mapbox_earcut available?
        if (cityjson.MODULE_EARCUT_AVAILABLE == False):
            str = "OBJ export skipped: Python module 'mapbox_earcut' missing (to triangulate faces)"
            click.echo(click.style(str, fg='red'))
            str = "Install it: https://github.com/skogler/mapbox_earcut_python"
            click.echo(str)
            return cm
        #-- output allowed
        extensions = ['.obj'] 
        #--
        print_cmd_status("Converting CityJSON to OBJ (%s)" % (filename))
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
            re = cm.export2obj()
            fo.write(re.getvalue())
        except IOError as e:
            raise click.ClickException('Invalid output file: "%s".\n%s' % (p, e))                
        return cm
    return processor


@cli.command('save')
@click.argument('filename')
@click.option('--indent', default=0)
@click.option('--textures', default=None, 
              type=str,
              help='Path to the new textures directory. This command copies the textures to a new location. Useful when creating an independent subset of a CityJSON file.')
def save_cmd(filename, indent, textures):
    """Save the city model to a CityJSON file."""
    def processor(cm):
        print_cmd_status("Saving CityJSON to a file (%s)" % (filename))
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
        print_cmd_status("Updating bbox")
        cm.update_bbox()
        return cm
    return processor


@cli.command('validate')
@click.option('--hide_errors', is_flag=True, help='Do not print all the errors.')
@click.option('--skip_schema', is_flag=True, help='Skip the schema validation (since it can be painfully slow).')
@click.option('--folder_schemas', help='Specify a folder where the schemas are (cityjson.json needs to be the master file).')
def validate_cmd(hide_errors, skip_schema, folder_schemas):
    """
    Validate the CityJSON file: (1) against its schemas; (2) extra validations.
    Only files with version >0.6 can be validated.

    The schemas are fetched automatically, based on the version of the file.
    It's possible to specify schemas with the '--folder_schemas' option.
    This is used when there are Extensions used.
    
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
                print_cmd_status('===== Validation (schemas: %s) =====' % (folder_schemas)) 
        else:
            print_cmd_status('===== Validation (schemas v%s) =====' % (cm.j['version']))
        #-- validate    
        bValid, woWarnings, errors, warnings = cm.validate(skip_schema=skip_schema, folder_schemas=folder_schemas)
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
        print_cmd_status('Merging files') 
        lsCMs = []
        g = glob.glob(filepattern)
        for i in g:
            try:
                f = click.open_file(i, mode='r')
                lsCMs.append(cityjson.reader(f))
            except ValueError as e:
                raise click.ClickException('%s: "%s".' % (e, input))
            except IOError as e:
                raise click.ClickException('Invalid file: "%s".' % (input))
        if len(lsCMs) == 0:
            click.echo("WARNING: No files to merge.")
        else:
            for i in lsCMs:
                click.echo("\t%s" % i)
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
        print_cmd_status('Subset of CityJSON') 
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
        print_cmd_status('Remove duplicate vertices')
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
        print_cmd_status('Remove orphan vertices')
        cm.remove_orphan_vertices()
        return cm
    return processor


@cli.command('remove_materials')
def remove_materials_cmd():
    """
    Remove all materials from a CityJSON file.
    """
    def processor(cm):
        print_cmd_status('Remove all material')
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
        print_cmd_status('Compressing the CityJSON (with %d digit)' % digit)
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
        print_cmd_status('Decompressing the CityJSON')
        if (cm.decompress() == False):
            click.echo("File is not compressed, nothing done.")
        return cm
    return processor


@cli.command('remove_textures')
def remove_textures_cmd():
    """
    Remove all textures from a CityJSON file.
    """
    def processor(cm):
        print_cmd_status('Remove all textures')
        cm.remove_textures()
        return cm
    return processor


@cli.command('assign_epsg')
@click.argument('newepsg', type=int)
def update_crs_cmd(newepsg):
    """
    Assign a (new) EPSG.
    Can be used to assign one to a file that doesn't have any, or update one.

    To reproject (and thus modify all the values of the coordinates) use reproject().
    """
    def processor(cm):
        print_cmd_status('Assign EPSG:%d' % newepsg)
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
        print_cmd_status('Reproject to EPSG:%d' % epsg)
        if (cm.get_epsg() == None):
            click.echo("WARNING: CityJSON has no EPSG defined, can't be reprojected.")
        else:    
            cm.reproject(epsg)
        return cm
    return processor


@cli.command('upgrade_version')
def upgrade_version_cmd():
    """
    Upgrade the CityJSON to the latest version.
    It takes care of *everything* (touch wood).

        $ cjio myfile.json upgrade_version
    """
    def processor(cm):
        vlatest = cityjson.CITYJSON_VERSIONS_SUPPORTED[-1]
        print_cmd_status('Upgrade CityJSON file to v%s' % vlatest)
        if (cm.upgrade_version(vlatest) == False):
            click.echo("WARNING: File cannot be upgraded to this version.")
        return cm
    return processor


@cli.command('locate_textures')
def locate_textures_cmd():
    """
    Output the location of the texture files.
    """
    def processor(cm):
        print_cmd_status('Locate the textures')
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
        print_cmd_status('Update location of textures')
        cm.update_textures_location(newlocation, relative=relative)
        return cm
    return processor
