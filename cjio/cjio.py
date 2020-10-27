import sys
import os.path

import click
import json
import copy
import glob
import re
import cjio
from cjio import cityjson, utils


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
        cjio example.json info validate
        cjio example.json assign_epsg 7145 remove_textures export output.obj
        cjio example.json subset --id house12 save out.json
    """
    context.obj = {"argument": input}


@cli.resultcallback()
def process_pipeline(processors, input, ignore_duplicate_keys):
    extensions = ['.json', '.off', '.poly'] #-- input allowed
    try:
        f = click.open_file(input, mode='r', encoding='utf-8-sig')
        extension = os.path.splitext(input)[1].lower()
        if extension not in extensions:
            raise IOError("File type not supported (only .json, .off, and .poly).")
        #-- OFF file
        if (extension == '.off'):
            utils.print_cmd_status("Converting %s to CityJSON" % (input))
            cm = cityjson.off2cj(f)
        #-- POLY file
        elif (extension == '.poly'):
            utils.print_cmd_status("Converting %s to CityJSON" % (input))
            cm = cityjson.poly2cj(f)            
        #-- CityJSON file
        else: 
            utils.print_cmd_status("Parsing %s" % (input))
            cm = cityjson.reader(file=f, ignore_duplicate_keys=ignore_duplicate_keys)
            if not isinstance(cm.get_version(), str):
                str1 = "CityJSON version should be a string 'X.Y' (eg '1.0')"
                raise click.ClickException(str1) 
            pattern = re.compile("^(\d\.)(\d)$") #-- correct pattern for version
            pattern2 = re.compile("^(\d\.)(\d\.)(\d)$") #-- wrong pattern with X.Y.Z
            if pattern.fullmatch(cm.get_version()) == None:
                if pattern2.fullmatch(cm.get_version()) != None:
                    str1 = "CityJSON version should be only X.Y (eg '1.0') and not X.Y.Z (eg '1.0.1')"
                    raise click.ClickException(str1)
                else:
                    str1 = "CityJSON version is wrongly formatted"
                    raise click.ClickException(str1)
            if (cm.get_version() not in cityjson.CITYJSON_VERSIONS_SUPPORTED):
                allv = ""
                for v in cityjson.CITYJSON_VERSIONS_SUPPORTED:
                    allv = allv + v + "/"
                str1 = "CityJSON version %s not supported (only versions: %s), not every operators will work.\nPerhaps it's time to upgrade cjio? 'pip install cjio -U'" % (cm.get_version(), allv)
                raise click.ClickException(str1)
            elif (cm.get_version() != cityjson.CITYJSON_VERSIONS_SUPPORTED[-1]):
                str1 = "v%s is not the latest version, and not everything will work.\n" % cm.get_version()
                str1 += "Upgrade the file with 'upgrade_version' command: 'cjio input.json upgrade_version save out.json'" 
                click.echo(click.style(str1, fg='red'))
            
    except ValueError as e:
        raise click.ClickException('%s: "%s".' % (e, input))
    except IOError as e:
        raise click.ClickException('Invalid file: "%s".\n%s' % (input, e))
    for processor in processors:
        cm = processor(cm)


@cli.command('info')
@click.pass_context
@click.option('--long', is_flag=True,
              help='More gory details about the file.')
def info_cmd(context, long):
    """Output info in simple JSON."""
    def processor(cm):
        click.echo(cm.get_info(long=long))
        return cm
    return processor


@cli.command('export')
@click.argument('filename')
@click.option('--format',
              type=click.Choice(['obj', 'stl', 'glb', 'b3dm']),
              help="Export format")
def export_cmd(filename, format):
    """Export the CityJSON to another format.

    OBJ, Binary glTF (glb), Batched 3DModel (b3dm), STL. Currently textures are not supported, sorry.
    """
    def exporter(cm):
        output = utils.verify_filename(filename)
        if output['dir']:
            os.makedirs(output['path'], exist_ok=True)
            input_filename = os.path.splitext(os.path.basename(cm.path))[0]
            output['path'] = os.path.join(output['path'], '{f}.{ext}'.format(
                f=input_filename, ext=format))
        else:
            os.makedirs(os.path.dirname(output['path']), exist_ok=True)
        if format.lower() == 'obj':
            utils.print_cmd_status("Exporting CityJSON to OBJ (%s)" % (output['path']))
            try:
                with click.open_file(output['path'], mode='w') as fo:
                    re = cm.export2obj()
                    fo.write(re.getvalue())
            except IOError as e:
                raise click.ClickException('Invalid output file: "%s".\n%s' % (output['path'], e))
        elif format.lower() == 'stl':
            utils.print_cmd_status("Exporting CityJSON to STL (%s)" % (output['path']))
            try:
                with click.open_file(output['path'], mode='w') as fo:
                    re = cm.export2stl()
                    fo.write(re.getvalue())
            except IOError as e:
                raise click.ClickException('Invalid output file: "%s".\n%s' % (output['path'], e))
        elif format.lower() == 'glb':
            fname = os.path.splitext(os.path.basename(output['path']))[0]
            bufferbin = "{}.glb".format(fname)
            binfile = os.path.join(os.path.dirname(output['path']), bufferbin)
            utils.print_cmd_status("Exporting CityJSON to glb %s" % binfile)
            glb = cm.export2gltf()
            # TODO B: how many buffer can there be in the 'buffers'?
            try:
                glb.seek(0)
                with click.open_file(binfile, mode='wb') as bo:
                    bo.write(glb.getvalue())
            except IOError as e:
                raise click.ClickException('Invalid output file: "%s".\n%s' % (binfile, e))
        elif format.lower() == 'b3dm':
            fname = os.path.splitext(os.path.basename(output['path']))[0]
            b3dmbin = "{}.b3dm".format(fname)
            binfile = os.path.join(os.path.dirname(output['path']), b3dmbin)
            b3dm = cm.export2b3dm()
            utils.print_cmd_status("Exporting CityJSON to b3dm %s" % binfile)
            utils.print_cmd_warning("Although the conversion works, the output is probably incorrect.")
            try:
                b3dm.seek(0)
                with click.open_file(binfile, mode='wb') as bo:
                    bo.write(b3dm.getvalue())
            except IOError as e:
                raise click.ClickException('Invalid output file: "%s".\n%s' % (binfile, e))


    def processor(cm):
        #-- mapbox_earcut available?
        if (cityjson.MODULE_EARCUT_AVAILABLE == False):
            str = "OBJ|glTF|b3dm export skipped: Python module 'mapbox_earcut' missing (to triangulate faces)"
            click.echo(click.style(str, fg='red'))
            str = "Install it: https://pypi.org/project/mapbox-earcut/"
            click.echo(str)
            return cm
        # NOTE BD: export_cmd can take a list of citymodels, which is the output of the partitioner
        if format.lower() == '3dtiles' or not isinstance(cm, list):
            exporter(cm)
        else:
            for subset in cm:
                exporter(subset)
        return cm
    return processor


@cli.command('save')
@click.argument('filename')
@click.option('--indent', is_flag=True,
              help='Indent the file. Helpful when you want to examine the file in a text editor.')
@click.option('--textures', default=None, 
              type=str,
              help='Path to the new textures directory. This command copies the textures to a new location. Useful when creating an independent subset of a CityJSON file.')
def save_cmd(filename, indent, textures):
    """Save the city model to a CityJSON file."""
    def saver(cm):
        output = utils.verify_filename(filename)
        if output['dir']:
            os.makedirs(output['path'], exist_ok=True)
            input_filename = os.path.splitext(os.path.basename(cm.path))[0]
            output['path'] = os.path.join(output['path'], '{f}.{ext}'.format(
                f=input_filename, ext='json'))
        else:
            os.makedirs(os.path.dirname(output['path']), exist_ok=True)
        
        try:
            if "metadata" in cm.j:
                cm.j["metadata"]["fileIdentifier"] = os.path.basename(output['path'])
        except:
            pass

        utils.print_cmd_status("Saving CityJSON to a file %s" % output['path'])
        try:
            fo = click.open_file(output['path'], mode='w')
            if textures:
                cm.copy_textures(textures, output['path'])
            if indent:
                json_str = json.dumps(cm.j, indent="\t")
                fo.write(json_str)
            else:
                json_str = json.dumps(cm.j, separators=(',',':'))
                fo.write(json_str)
        except IOError as e:
            raise click.ClickException('Invalid output file: %s \n%s' % (output['path'], e))

    def processor(cm):
        saver(cm)
        return cm
    return processor

@cli.command('validate')
@click.option('--hide_errors', is_flag=True, help='Do not print all the errors.')
@click.option('--skip_schema', is_flag=True, help='Skip the schema validation (since it can be painfully slow).')
@click.option('--folder_schemas', help='Specify a folder where the schemas are (cityjson.json needs to be the master file).')
def validate_cmd(hide_errors, skip_schema, folder_schemas):
    """
    Validate the CityJSON file: (1) against its schemas; (2) extra validations.

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
                utils.print_cmd_status('===== Validation (with provided schemas) =====')
        else:
            utils.print_cmd_status('===== Validation (with official CityJSON schemas) =====')
        #-- validate    
        bValid, woWarnings, errors, warnings = cm.validate(skip_schema=skip_schema, folder_schemas=folder_schemas)
        click.echo('=====')
        if bValid == True:
            click.echo(click.style('File is valid', fg='green'))
        else:    
            click.echo(click.style('File is invalid', fg='red'))
        if woWarnings == True:
            click.echo(click.style('File has no warnings', fg='green'))
        else:
            click.echo(click.style('File has warnings', fg='red'))
        if not hide_errors and bValid is False:
            click.echo("--- ERRORS (total = %d) ---" % len(errors))
            for e in errors:
                click.echo(e)
                # for l in e:
                    # click.echo(l)
        if not hide_errors and woWarnings is False:
            click.echo("--- WARNINGS ---")
            for e in warnings:
                click.echo(e)
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
        utils.print_cmd_status('Merging files')
        lsCMs = []
        g = glob.glob(filepattern)
        for i in g:
            try:
                f = click.open_file(i, mode='r', encoding='utf-8-sig')
                lsCMs.append(cityjson.reader(f))
            except ValueError as e:
                raise click.ClickException('%s: "%s".' % (e, input))
            except IOError as e:
                raise click.ClickException('Invalid file: "%s".' % (input))
        if len(lsCMs) == 0:
            click.echo("WARNING: No files to merge.")
        else:
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
@click.option('--exclude', is_flag=True, help='Excludes the selection, thus delete the selected object(s).')
def subset_cmd(id, bbox, random, cotype, exclude):
    """
    Create a subset of a CityJSON file.
    One can select City Objects by
    (1) IDs of City Objects;
    (2) bbox;
    (3) City Object type;
    (4) randomly.

    These can be combined, except random which overwrites others.

    Option '--exclude' excludes the selected objects, or "reverse" the selection.
    """
    def processor(cm):
        utils.print_cmd_status('Subset of CityJSON')
        s = copy.deepcopy(cm)
        if random is not None:
            s = s.get_subset_random(random, exclude=exclude)
            return s
        if len(id) > 0:
            s = s.get_subset_ids(id, exclude=exclude)
        if len(bbox) > 0:
            s = s.get_subset_bbox(bbox, exclude=exclude)
        if cotype is not None:
            s = s.get_subset_cotype(cotype, exclude=exclude)
        return s 
    return processor


@cli.command('clean')
@click.option('--digit', default=3, type=click.IntRange(1, 10), help='Number of digit to use to compare vertices (default=3).')
def clean_cmd(digit):
    """
    Clean 
    =
    remove_duplicate_vertices
    +
    remove_orphan_vertices    
    """
    def processor(cm):
        utils.print_cmd_status('Clean the file')
        cm.remove_duplicate_vertices(digit)
        cm.remove_orphan_vertices()
        return cm
    return processor


@cli.command('remove_duplicate_vertices')
@click.argument('precision')
def remove_duplicate_vertices_cmd(precision):
    """
    Remove duplicate vertices a CityJSON file.
    Only the geometry vertices are processed,
    and not those of the textures/templates.
    """
    def processor(cm):
        utils.print_cmd_status('Remove duplicate vertices')
        cm.remove_duplicate_vertices(precision)
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
        utils.print_cmd_status('Remove orphan vertices')
        cm.remove_orphan_vertices()
        return cm
    return processor


@cli.command('remove_materials')
def remove_materials_cmd():
    """
    Remove all materials from a CityJSON file.
    """
    def processor(cm):
        utils.print_cmd_status('Remove all material')
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
        utils.print_cmd_status('Compressing the CityJSON (with %d digit)' % digit)
        if cm.compress(digit) == False:
            click.echo("WARNING: CityJSON already compressed.")
        return cm
    return processor


@cli.command('decompress')
def decompress_cmd():
    """
    Decompress a CityJSON file, ie remove the "tranform".
    """
    def processor(cm):
        utils.print_cmd_status('Decompressing the CityJSON')
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
        utils.print_cmd_status('Remove all textures')
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
        utils.print_cmd_status('Assign EPSG:%d' % newepsg)
        cm.set_epsg(newepsg)
        return cm
    return processor


@cli.command('reproject')
@click.argument('epsg', type=int)
def update_crs_cmd(epsg):
    """
    Reproject the CityJSON to a new EPSG.
    The current file must have an EPSG defined (do it with function assign_epsg).
    """
    def processor(cm):
        if (cityjson.MODULE_PYPROJ_AVAILABLE == False):
            str = "Reprojection skipped: Python module 'pyproj' missing (to reproject coordinates)"
            click.echo(click.style(str, fg='red'))
            str = "Install it: https://pypi.org/project/pyproj/"
            click.echo(str)
            return cm
        utils.print_cmd_status('Reproject to EPSG:%d' % epsg)
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
        utils.print_cmd_status('Upgrade CityJSON file to v%s' % vlatest)
        re, reasons = cm.upgrade_version(vlatest)
        if (re == False):
            click.echo(click.style("WARNING: %s" % (reasons), fg='red'))
        return cm
    return processor


@cli.command('locate_textures')
def locate_textures_cmd():
    """
    Output the location of the texture files.
    """
    def processor(cm):
        utils.print_cmd_status('Locate the textures')
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
        utils.print_cmd_status('Update location of textures')
        cm.update_textures_location(newlocation, relative=relative)
        return cm
    return processor


@cli.command('extract_lod')
@click.argument('lod', type=int)
def extract_lod_cmd(lod):
    """
    Extract only one LoD for a dataset.
    To use on datasets having more than one LoD for the city objects.
    For each city object, it keeps only the LoD passed as parameter,
    if a city object doesn't have this LoD then it is deleted.
    """
    def processor(cm):
        utils.print_cmd_status('Extract LoD:%s' % lod)
        cm.extract_lod(lod)
        return cm
    return processor


@cli.command('translate')
@click.option('--values', nargs=3, type=float, help='(x, y, z)')
def translate_cmd(values):
    """
    Translate the file by its (-minx, -miny, -minz).

    Three values can also be given, eg: 'translate --values -100 -25 -1'
    """
    def processor(cm):
        if len(values) == 0:
           bbox = cm.translate(values=[], minimum_xyz=True)
        else:
            bbox = cm.translate(values=values, minimum_xyz=False)
        utils.print_cmd_status('Translating the file by: (%f, %f, %f)' % (bbox[0], bbox[1], bbox[2]))
        return cm
    return processor


@cli.command('update_metadata')
@click.option('--overwrite', is_flag=True, help='Overwrite existing values.')
def update_metadata_cmd(overwrite):
    """
    Update the metadata for properties/values that can be
    computed. Updates the dataset.
    """
    def processor(cm):
        utils.print_cmd_status('Update the metadata')
        re, errors = cm.update_metadata(overwrite)

        for e in errors:
            utils.print_cmd_warning(e)


@cli.command('get_metadata')
def get_metadata_cmd():
    """
    Shows the metadata of this dataset.

    The difference between 'info' and this command is that this
    command lists the "pure" metadata as stored in the file.
    The 'info' command should be used when an overview of the
    file is needed.
    """
    def processor(cm):
        if cm.has_metadata():
            click.echo_via_pager(json.dumps(cm.get_metadata(), indent=2))
        else:
            utils.print_cmd_warning("You are missing metadata! Quickly! Run 'update_metadata' before it's too late!")
    return processor


# Needed for the executable created by PyInstaller
if getattr(sys, 'frozen', False):
    cli(sys.argv[1:])
