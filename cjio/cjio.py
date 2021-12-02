import sys
import os.path
from os import linesep

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
@click.version_option(version=cjio.__version__, prog_name=cityjson.CITYJSON_VERSIONS_SUPPORTED[-1], message="cjio v%(version)s; supports CityJSON v%(prog)s")
@click.argument('input', cls=PerCommandArgWantSubCmdHelp)
@click.option('--ignore_duplicate_keys', is_flag=True, help='Load a CityJSON file even if some City Objects have the same IDs (technically invalid file)')
@click.pass_context
def cli(context, input, ignore_duplicate_keys):
    """Process and manipulate a CityJSON model, and allow
    different outputs. The different operators can be chained
    to perform several processing in one step, the CityJSON model
    goes through the different operators.

    To get help on specific command, eg for 'validate':

    \b
        cjio validate --help

    Usage examples:

    \b
        cjio myfile.city.json info 
        cjio myfile.city.json validate
        cjio myfile.city.json subset --id house12 save out.city.json
        cjio myfile.city.json crs_assign 7145 textures_remove export --format obj output.obj
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
                str1 += "Upgrade the file with 'upgrade' command: 'cjio input.json upgrade save out.json'" 
                utils.print_cmd_alert(str1)
    except ValueError as e:
        raise click.ClickException('%s: "%s".' % (e, input))
    except IOError as e:
        raise click.ClickException('Invalid file: "%s".\n%s' % (input, e))
    for processor in processors:
        cm = processor(cm)


@cli.command('info')
@click.pass_context
@click.option('--long', is_flag=True, help='More gory details about the file.')
def info_cmd(context, long):
    """Output information about the dataset."""
    def processor(cm):
        utils.print_cmd_status('Information ⬇️')
        s = linesep.join(cm.get_info(long=long))
        click.echo(s)
        utils.print_cmd_status('Information ⬆️')
        return cm
    return processor


@cli.command('export')
@click.argument('filename')
@click.option('--format',
              type=click.Choice(['obj', 'jsonl', 'stl', 'glb', 'b3dm']),
              required=True,
              help="Export format")
def export_cmd(filename, format):
    """Export to another format.

    OBJ, Binary glTF (glb), Batched 3DModel (b3dm), STL, JSONL (JSON Lines, for streaming). 
    
    Currently textures are not supported, sorry.

    Usage examples:

    \b
        cjio myfile.city.json export --format obj myfile.obj 
        cjio myfile.city.json export --format jsonl myfile.txt 
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
        elif format.lower() == 'jsonl':
            utils.print_cmd_status("Exporting CityJSON to JSON Lines (%s)" % (output['path']))
            try:
                with click.open_file(output['path'], mode='w') as fo:
                    re = cm.export2jsonl()
                    fo.write(re.getvalue())
            except IOError as e:
                raise click.ClickException('Invalid output file: "%s".\n%s' % (output['path'], e))

    def processor(cm):
        #-- mapbox_earcut available?
        if (format != 'jsonl') and (cityjson.MODULE_EARCUT_AVAILABLE == False):
            str = "OBJ|glTF|b3dm export skipped: Python module 'mapbox_earcut' missing (to triangulate faces)"
            utils.print_cmd_alert(str)
            str = "Install it: https://pypi.org/project/mapbox-earcut/"
            utils.print_cmd_warning(str)
            raise click.ClickException('Abort.')
        else:
            exporter(cm)
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
    """Save to a CityJSON file."""
    def saver(cm):
        output = utils.verify_filename(filename)
        if output['dir']:
            os.makedirs(output['path'], exist_ok=True)
            input_filename = os.path.splitext(os.path.basename(cm.path))[0]
            output['path'] = os.path.join(output['path'], '{f}.{ext}'.format(
                f=input_filename, ext='json'))
        else:
            os.makedirs(os.path.dirname(output['path']), exist_ok=True)
        
        # try:
        #     if "metadata" in cm.j:
        #         cm.j["metadata"]["fileIdentifier"] = os.path.basename(output['path'])
        # except:
        #     pass

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
def validate_cmd():
    """
    Validate the CityJSON: 
    (1) against its schemas
    (2) against the (potential) Extensions schemas
    (3) extra validations
    
    (see https://github.com/cityjson/cjval#what-is-validated-exactly for details)

    The Extensions in the files are fetched automatically.

    \b
        $ cjio myfile.city.json validate
    """
    def processor(cm):
        if (cityjson.MODULE_CJVAL_AVAILABLE == False):
            str = "Validation skipped: Python module 'cjvalpy' not installed"
            utils.print_cmd_alert(str)
            str = "To install it: https://www.github.com/cityjson/cjvalpy"
            utils.print_cmd_warning(str)
            str = "Alternatively use the web-app: https://validator.cityjson.org"
            utils.print_cmd_warning(str)
            raise click.ClickException('Abort.')
        utils.print_cmd_status('Validation (with official CityJSON schemas)')
        try:
            re = cm.validate()
            click.echo(re)
        except Exception as e:
            utils.print_cmd_alert("Error: {}".format(e))
        return cm
    return processor


@cli.command('merge')
@click.argument('filepattern')
def merge_cmd(filepattern):
    """
    Merge the current CityJSON with other ones.
    All City Objects with their textures/materials/templates are handled.
    
    Possible to give a wildcard but put it between quotes:

        $ cjio myfile.city.json merge '/home/elvis/temp/*.json' save merged.city.json
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
@click.option('--bbox', nargs=4, type=float, help='2D bbox: minx miny maxx maxy.')
@click.option('--random', type=int, help='Number of random City Objects to select.')
@click.option('--cotype',
    type=click.Choice(['Building', 'Bridge', 'Road', 'TransportSquare', 'LandUse', 'Railway', 'TINRelief', 'WaterBody', 'PlantCover', 'SolitaryVegetationObject', 'CityFurniture', 'GenericCityObject', 'Tunnel']), 
    help='The City Object type')
@click.option('--exclude', is_flag=True, help='Excludes the selection, thus delete the selected object(s).')
def subset_cmd(id, bbox, random, cotype, exclude):
    """
    Create a subset, City Objects can be selected by:
    (1) IDs of City Objects;
    (2) bbox;
    (3) City Object type;
    (4) randomly.

    These can be combined, except random which overwrites others.

    Option '--exclude' excludes the selected objects, or "reverse" the selection.

    Usage examples:

    \b
        cjio myfile.city.json subset --bbox 104607 490148 104703 490257 save out.city.json 
        cjio myfile.city.json subset --id house12 save out.city.json
        cjio myfile.city.json subset --random 5 save out.city.json
        cjio myfile.city.json subset --cotype LandUse save out.city.json
    """
    def processor(cm):
        utils.print_cmd_status('Subset of CityJSON')
        s = copy.deepcopy(cm)
        if random is not None:
            s = s.get_subset_random(random, exclude=exclude)
            return s
        elif id is not None and len(id) > 0:
            s = s.get_subset_ids(id, exclude=exclude)
        elif bbox is not None and len(bbox) > 0:
            s = s.get_subset_bbox(bbox, exclude=exclude)
        elif cotype is not None:
            s = s.get_subset_cotype(cotype, exclude=exclude)
        else:
            click.BadArgumentUsage('You must provide one of the options for subset; --id, --bbox, --random, --cotype')
        return s 
    return processor


@cli.command('vertices_clean')
def vertices_clean_cmd():
    """
    Remove duplicate vertices + orphan vertices    
    """
    def processor(cm):
        utils.print_cmd_status('Clean the file')
        cm.remove_duplicate_vertices()
        cm.remove_orphan_vertices()
        return cm
    return processor

@cli.command('materials_remove')
def materials_remove_cmd():
    """
    Remove all materials.
    """
    def processor(cm):
        utils.print_cmd_status('Remove all material')
        cm.remove_materials()
        return cm
    return processor

@cli.command('textures_remove')
def textures_remove_cmd():
    """
    Remove all textures.
    """
    def processor(cm):
        utils.print_cmd_status('Remove all textures')
        cm.remove_textures()
        return cm
    return processor


@cli.command('crs_assign')
@click.argument('newepsg', type=int)
def crs_assign_cmd(newepsg):
    """
    Assign a (new) CRS (an EPSG).
    Can be used to assign one to a file that doesn't have any, or update one.

    To reproject (and thus modify all the values of the coordinates) use reproject().
    """
    def processor(cm):
        utils.print_cmd_status('Assign EPSG:%d' % newepsg)
        cm.set_epsg(newepsg)
        return cm
    return processor


@cli.command('crs_reproject')
@click.argument('epsg', type=int)
def crs_reproject_cmd(epsg):
    """
    Reproject to a new EPSG.
    The current CityJSON must have an EPSG defined 
    (which can be done with function epsg_assign).
    """
    def processor(cm):
        if (cityjson.MODULE_PYPROJ_AVAILABLE == False):
            str = "Reprojection skipped: Python module 'pyproj' missing (to reproject coordinates)"
            utils.print_cmd_alert(str)
            str = "Install it: https://pypi.org/project/pyproj/"
            utils.print_cmd_warning(str)
            raise click.ClickException('Abort.')
        utils.print_cmd_status('Reproject to EPSG:%d' % epsg)
        if (cm.get_epsg() == None):
            click.echo("WARNING: CityJSON has no EPSG defined, can't be reprojected.")
        else:    
            cm.reproject(epsg)
        return cm
    return processor


@cli.command('upgrade')
@click.option('--digit', default=3, type=click.IntRange(1, 12), help='Number of digit to keep to compress.')
def upgrade_cmd(digit):
    """
    Upgrade the CityJSON to the latest version.
    It takes care of *everything* (touch wood).

        $ cjio myfile.city.json upgrade save upgraded.city.json
    
    For v1.1+, the file needs to be compressed, and you can 
    speficy the number of digits to keep (default=3)

        $ cjio myfile.city.json upgrade --digit 2 save upgraded.city.json
    """
    def processor(cm):
        vlatest = cityjson.CITYJSON_VERSIONS_SUPPORTED[-1]
        utils.print_cmd_status('Upgrade CityJSON file to v%s' % vlatest)
        re, reasons = cm.upgrade_version(vlatest, digit)
        if (re == False):
            utils.print_cmd_warning("WARNING: %s" % (reasons))
        return cm
    return processor


@cli.command('textures_locate')
def textures_locate_cmd():
    """
    Output the location of the texture files.
    """
    def processor(cm):
        utils.print_cmd_status('Locate the textures')
        loc = cm.get_textures_location()
        click.echo(loc)
        return cm
    return processor


@cli.command('textures_update')
@click.argument('newlocation', type=str)
@click.option('--relative', is_flag=True, help='Convert texture file paths to relative paths.')
def textures_update_cmd(newlocation, relative):
    """
    Update the location of the texture files.
    Can be used if the texture files were moved to new directory.
    """
    def processor(cm):
        utils.print_cmd_status('Update location of textures')
        cm.update_textures_location(newlocation, relative=relative)
        return cm
    return processor


@cli.command('lod_filter')
@click.argument('lod', type=str)
def lod_filter_cmd(lod):
    """
    Filter only one LoD for a dataset.
    To use on datasets having more than one LoD for the city objects.
    For each city object, it keeps only the geometries having the LoD
    passed as parameter; if a city object doesn't have this LoD then 
    it ends up with an empty geometry.

        $ cjio myfile.city.json lod_filter 2.2 save myfile_lod2.city.json
    
    """
    def processor(cm):
        utils.print_cmd_status('Filter LoD: "%s"' % lod)
        cm.filter_lod(lod)
        return cm
    return processor

@cli.command('attribute_remove')
@click.argument('attr', type=str, nargs=1)
def attribute_remove_cmd(attr):
    """
    Remove an attribute. 
    If it's not present nothing is done.
    That's it.    

        $ cjio myfile.city.json attribute_remove roofType info
    """
    def processor(cm):
        utils.print_cmd_status('Remove attribute: "%s"' % attr)
        cm.remove_attribute(attr)
        return cm
    return processor


@cli.command('attribute_rename')
@click.argument('oldattr', type=str, nargs=1)
@click.argument('newattr', type=str, nargs=1)
def attribute_rename_cmd(oldattr, newattr):
    """
    Rename an attribute. 
    If it's not present nothing is done, and its value is kept.
    That's it.    

        $ cjio myfile.city.json attribute_rename oldAttr newAttr info
    """
    def processor(cm):
        utils.print_cmd_status('Rename attribute: "%s" => "%s"' % (oldattr, newattr))
        cm.rename_attribute(oldattr, newattr)
        return cm
    return processor

@cli.command('crs_translate')
@click.option('--values', nargs=3, type=float, help='(x, y, z)')
def crs_translate_cmd(values):
    """
    Translate the coordinates. 
    All are moved (-minx, -miny, -minz) of the model.
    Three values can also be given, eg: 

        $ cjio myfile.city.json crs_translate --values -100 -25 -1 save out.city.json
    """
    def processor(cm):
        if len(values) == 0:
           bbox = cm.translate(values=[], minimum_xyz=True)
        else:
            bbox = cm.translate(values=values, minimum_xyz=False)
        utils.print_cmd_status('Translating the file by: (%f, %f, %f)' % (bbox[0], bbox[1], bbox[2]))
        return cm
    return processor


@cli.command('metadata_create')
def metadata_create_cmd():
    """
    Add the +metadata-extended properties.
    This is the MetadataExtended Extension 
    (https://github.com/cityjson/metadata-extended).
    Modify/update the dataset.
    """
    def processor(cm):
        utils.print_cmd_status('Create the +metadata-extended and populate it')
        _, errors = cm.update_metadata_extended(overwrite=True)
        for e in errors:
            utils.print_cmd_warning(e)
        return cm
    return processor


@cli.command('metadata_update')
@click.option('--overwrite', is_flag=True, help='Overwrite existing values.')
def metadata_update_cmd(overwrite):
    """
    Update the +metadata-extended.
    Properties that can be computed are updated. 
    Modify/update the dataset.
    """
    def processor(cm):
        utils.print_cmd_status('Update the +metadata-extended')
        _, errors = cm.update_metadata_extended(overwrite)
        for e in errors:
            utils.print_cmd_warning(e)
        return cm
    return processor


@cli.command('metadata_get')
def metadata_get_cmd():
    """
    Shows the metadata and +metadata-extended of this dataset
    (they are merged in one JSON object)

    The difference between 'info' and this command is that this
    command lists the "pure" metadata as stored in the file.
    The 'info' command should be used when an overview of the
    file is needed.
    """
    def processor(cm):
        j = {}
        if cm.has_metadata():
            j.update(cm.get_metadata())
        if cm.has_metadata_extended():
            j.update(cm.get_metadata_extended())
        click.echo(json.dumps(j, indent=2))
        return cm
    return processor


@cli.command('metadata_remove')
def metadata_remove_cmd():
    """
    Remove the +metadata-extended properties.
    Modify/update the dataset.
    """
    def processor(cm):
        utils.print_cmd_status('Remove the +metadata-extended property')
        cm.metadata_extended_remove()
        return cm
    return processor

@cli.command('triangulate')
def triangulate_cmd():
    """
    Triangulate every surface.

    Takes care of updating: (1) semantics; (2) textures; (3) material.

        $ cjio myfile.city.json triangulate save mytriangles.city.json 
    """
    #-- mapbox_earcut available?
    def processor(cm):
        utils.print_cmd_status('Triangulate the CityJSON file')
        if (cityjson.MODULE_EARCUT_AVAILABLE == False):
            str = "Cannot triangulate: Python module 'mapbox_earcut' missing. Stopping here."
            utils.print_cmd_alert(str)
            str = "Install it: https://pypi.org/project/mapbox-earcut/"
            utils.print_cmd_alert(str)
            raise click.ClickException('Abort.')
            return cm
        if not(cm.is_triangulated()):
            cm.triangulate()
        else:
            utils.print_cmd_status('This file is already triangulated!')
        return cm
    return processor


# Needed for the executable created by PyInstaller
if getattr(sys, 'frozen', False):
    cli(sys.argv[1:])
