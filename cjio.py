
import click
import json
import sys
import cityjson

# https://stackoverflow.com/questions/47437472/in-python-click-how-do-i-see-help-for-subcommands-whose-parents-have-required

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
# update_crs
# remove_duplicate_vertices
# remove_orphan_vertices
# apply_material(rule, color=red)


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
@click.argument('input', cls=PerCommandArgWantSubCmdHelp)
@click.pass_context
def cli(context, input):
    """Processes a CityJSON and allows different outputs.
    The operators can be chained to perform several processing
    in one step. One commands feeds into the next.

    Example:

    \b
        cjio example.json compress --digit 3 info
        cjio example.json remove_textures subset 100 100 400 400 compress save out.json
    """
    context.obj = {"argument": input}


@cli.resultcallback()
@click.pass_context
def process_pipeline(context, processors, input):
    try:
        f = click.open_file(input, mode='r')
        cm = cityjson.CityJSON(f)
    except ValueError as e:
        click.echo(context.get_usage() + "\n")
        raise click.ClickException('%s: "%s".' % (e, input))
    except IOError as e:
        click.echo(context.get_usage() + "\n")
        raise click.ClickException('Invalid file: "%s".' % (input))
    for processor in processors:
        cm = processor(cm)


@cli.command('info')
@click.pass_context
def info_cmd(context):
    """Outputs info about CityJSON file (in JSON)"""
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
            json_str = json.dumps(cm.j)
        else:
            json_str = json.dumps(cm.j, indent=indent)
        # filen = open(filename, "w")
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
def validate_cmd(hide_errors):
    """
    Validate the file against its schema.
    """
    def processor(cm):
        bValid, errors = cm.validate()
        click.echo('===== Schema Validation =====')
        click.echo(bValid)
        if not hide_errors:
            click.echo("ERRORS:")
            click.echo(errors)
        click.echo('=============================')
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
        if "metadata" not in cm.j:
            cm.j["metadata"] = {}
        if "crs" not in cm.j["metadata"]:
            cm.j["metadata"]["crs"] = {} 
        if "epsg" not in cm.j["metadata"]["crs"]:
            cm.j["metadata"]["crs"]["epsg"] = None
        cm.j["metadata"]["crs"]["epsg"] = newcrs
        return cm
    return processor



if __name__ == '__main__':
    cli()    