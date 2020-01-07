
import os.path

import click
import json
import copy
import glob
import cjio
from cjio import cityjson, tiling, utils


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
            if (cm.get_version() not in cityjson.CITYJSON_VERSIONS_SUPPORTED):
                allv = ""
                for v in cityjson.CITYJSON_VERSIONS_SUPPORTED:
                    allv = allv + v + "/"
                str = "CityJSON version %s not supported (only versions: %s), not every operators will work.\nPerhaps it's time to upgrade cjio? 'pip install cjio -U'" % (cm.get_version(), allv)
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
@click.option('--long', is_flag=True,
              help='More gory details about the file.')
def info_cmd(context, long):
    """Output info in simple JSON."""
    def processor(cm):
        if isinstance(cm, list):
            for subset in cm:
                click.echo("=============== City model: %s ===============" % subset.path)
                click.echo(subset.get_info(long=long))
        else:
            click.echo(cm.get_info(long=long))
        return cm
    return processor


@cli.command('export')
@click.argument('filename')
@click.option('--format',
              type=click.Choice(['obj', 'glb', 'b3dm', '3dtiles']),
              help="Export format")
def export_cmd(filename, format):
    """Export the CityJSON to another format.

    OBJ, Binary glTF (glb), Batched 3DModel, Cesium 3D Tiles. Currently textures are not supported, sorry.
    """
    def exporter(cm):
        # TODO B: refactor for handling partitions for each format
        output = utils.verify_filename(filename)
        if output['dir']:
            os.makedirs(output['path'], exist_ok=True)
            if isinstance(cm, list):
                pass
            else:
                input_filename = os.path.splitext(os.path.basename(cm.path))[0]
                output['path'] = os.path.join(output['path'], '{f}.{ext}'.format(
                    f=input_filename, ext=format))
        else:
            os.makedirs(os.path.dirname(output['path']), exist_ok=True)
        if format.lower() == 'obj':
            utils.print_cmd_status("Exporting CityJSON to OBJ (%s)" % (output['path']))
            if isinstance(cm, list):
                click.ClickException("Not implemented for exporting multiple citymodels")
            try:
                fo = click.open_file(output['path'], mode='w')
                re = cm.export2obj()
                # TODO B: why don't you close the file @hugoledoux?
                fo.write(re.getvalue())
            except IOError as e:
                raise click.ClickException('Invalid output file: "%s".\n%s' % (output['path'], e))
        elif format.lower() == 'glb':
            if isinstance(cm, list):
                click.ClickException("Not implemented for exporting multiple citymodels")
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
            if isinstance(cm, list):
                click.ClickException("Not implemented for exporting multiple citymodels")
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
        elif format.lower() == '3dtiles':
            utils.print_cmd_status("Exporting CityJSON to 3dtiles")
            utils.print_cmd_warning("Although the conversion works, the output is probably incorrect.")
            tileset = tiling.generate_tileset_json()
            if isinstance(cm, list):
                bbox_list = []
                for i,subset in enumerate(cm):
                    fname = os.path.splitext(os.path.basename(subset.path))[0]
                    b3dmbin = "{}.b3dm".format(fname)
                    binfile = os.path.join(output['path'], b3dmbin)
                    bbox = subset.update_bbox()
                    b3dm = subset.export2b3dm()
                    bbox_list.append(bbox)
                    tile = tiling.generate_tile_json()
                    tile['boundingVolume']['box'] = tiling.compute_obb(bbox)
                    tile['content']['uri'] = b3dmbin
                    tileset['root']['children'].append(tile)
                    utils.print_cmd_substatus("Exporting b3dm %s" % binfile)
                    try:
                        b3dm.seek(0)
                        with click.open_file(binfile, mode='wb') as bo:
                            bo.write(b3dm.getvalue())
                    except IOError as e:
                        raise click.ClickException('Invalid output file: "%s".\n%s' % (binfile, e))
                tilesetfile = os.path.join(output['path'], 'tileset.json')
                bbox_root = tiling.compute_root_obb(bbox_list)
                tileset['root']['boundingVolume']['box'] = tiling.compute_obb(bbox_root)
                del tileset['root']['content']
                utils.print_cmd_substatus("Exporting tileset.json %s" % tilesetfile)
                try:
                    with click.open_file(tilesetfile, mode='w') as fo:
                        json_str = json.dumps(tileset, indent=2)
                        fo.write(json_str)
                except IOError as e:
                    raise click.ClickException('Invalid output file: %s \n%s' % (output['path'], e))
            else:
                # if the citymodel is not partitioned, then the whole model is the root tile
                # if (cm.get_epsg() == None):
                #     raise click.ClickException("CityJSON has no EPSG defined, can't be reprojected.")
                # elif cm.get_epsg() != 4326:
                #     utils.print_cmd_status("Reprojecting CityJSON to EPSG:4326")
                #     cm.reproject(3857)
                fname = os.path.splitext(os.path.basename(output['path']))[0]
                b3dmbin = "{}.b3dm".format(fname)
                binfile = os.path.join(os.path.dirname(output['path']), b3dmbin)
                tilesetfile = os.path.join(os.path.dirname(output['path']), 'tileset.json')
                bbox = cm.update_bbox()
                b3dm = cm.export2b3dm()
                bbox_root = [coordinate * 1.1 for coordinate in bbox] # methinks the root boundingVolume should be larger than that of the children, even when there is only one child
                tileset['root']['boundingVolume']['box'] = tiling.compute_obb(bbox_root)
                tileset['root']['content']['boundingVolume']['box'] = tiling.compute_obb(bbox)
                tileset['root']['content']['uri'] = b3dmbin
                del tileset['root']['children']
                utils.print_cmd_status("Exporting b3dm %s" % binfile)
                try:
                    b3dm.seek(0)
                    with click.open_file(binfile, mode='wb') as bo:
                        bo.write(b3dm.getvalue())
                except IOError as e:
                    raise click.ClickException('Invalid output file: "%s".\n%s' % (binfile, e))
                utils.print_cmd_status("Exporting tileset.json %s" % tilesetfile)
                try:
                    with click.open_file(tilesetfile, mode='w') as fo:
                        json_str = json.dumps(tileset, indent=2)
                        fo.write(json_str)
                except IOError as e:
                    raise click.ClickException('Invalid output file: %s \n%s' % (output['path'], e))


    def processor(cm):
        #-- mapbox_earcut available?
        if (cityjson.MODULE_EARCUT_AVAILABLE == False):
            str = "OBJ|glTF|b3dm export skipped: Python module 'mapbox_earcut' missing (to triangulate faces)"
            click.echo(click.style(str, fg='red'))
            str = "Install it: https://github.com/skogler/mapbox_earcut_python"
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
        if isinstance(cm, list):
            for subset in cm:
                saver(subset)
        else:
            saver(cm)
        return cm
    return processor


@cli.command('update_bbox')
def update_bbox_cmd():
    """
    Update the bbox of a CityJSON file.
    If there is none then it is added.
    """
    def processor(cm):
        utils.print_cmd_status("Updating bbox")
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

@cli.command('partition')
@click.option('--depth', type=int, help='Number of times to subdivide the BBOX.')
@click.option('--cellsize', nargs=2, type=float, help='Size of the cells in the partitioning (length x, length y).')
def partition_cmd(depth, cellsize):
    """
    Partition the city model into tiles.
    One can provide either

    (1) --depth as the depth of the quadtree that is generated from the BBOX of the input citymodel. For example --depth 2 yields 16 cells;

        $ cjio myfile.json partition --depth 2

    (2) --cellsize as the approx. size of cells that partition the BBOX of the input citymodel.

        $ cjio myfile.json partition --cellsize 500.0 500.0
    """
    def processor(cm):
        utils.print_cmd_status('===== Partitioning CityJSON =====')
        if (cellsize and depth):
            raise click.ClickException("Please choose either --depth or --cellsize")
        if cellsize:
            raise click.ClickException("Sorry, --cellsize is not implemented yet")
        bbox = cm.update_bbox()
        grid_idx = tiling.create_grid(bbox, depth)
        partitions = tiling.partitioner(cm, grid_idx)

        textures = None
        indent = 0

        # NOTE BD: for now i store the subsets in the list to they can be passed forward to the exporter, but probably there more memory efficient ways to do this
        cms = []
        input_filename = os.path.splitext(os.path.basename(cm.path))[0]
        for idx, colist in partitions.items():
            s = cm.get_subset_ids(colist)
            filename = '{}_{}.json'.format(input_filename, idx)
            s.path = filename
            cms.append(s)
        return cms
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
def clean_cmd():
    """
    Clean 
    =
    remove_duplicate_vertices
    +
    remove_orphan_vertices    
    """
    def processor(cm):
        utils.print_cmd_status('Clean the file')
        cm.remove_duplicate_vertices()
        cm.remove_orphan_vertices()
        return cm
    return processor


@cli.command('remove_duplicate_vertices')
def remove_duplicate_vertices_cmd():
    """
    Remove duplicate vertices a CityJSON file.
    Only the geometry vertices are processed,
    and not those of the textures/templates.
    """
    def processor(cm):
        utils.print_cmd_status('Remove duplicate vertices')
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
