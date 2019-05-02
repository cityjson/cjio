"""Various utility functions"""

import os.path
from click import ClickException
from click import echo, style

def generate_filepath(filename, extension):
    # TODO B: write function
    """Generate a full path to the output file"""
    output = verify_filename(filename)
    filepath = output
    return filepath

def verify_filename(filename):
    """Verify if the provided output filename is a file or a directory"""
    res = {'dir': False, 'path': ''}
    if os.path.isdir(filename):
        res['dir'] = True
        absp = os.path.abspath(filename)
        if os.path.exists(absp):
            res['path'] = absp
        else:
            raise ClickException("Couldn't expand %s to absolute path" % filename)
    else:
        base = os.path.basename(filename)
        dirname = os.path.abspath(os.path.dirname(filename))
        # parent directory must exist, we don't recurse further
        if not os.path.exists(dirname):
            raise ClickException('Path does not exist: "%s"' % (dirname))
        fname, extension = os.path.splitext(base)
        res['path'] = os.path.join(dirname, base)
        if len(extension) == 0:
            res['dir'] = True
        else:
            res['dir'] = False
    return res


def print_cmd_status(s):
    echo(style(s, bg='cyan', fg='black'))

def print_cmd_substatus(s):
    echo(style(s, fg='cyan'))

def print_cmd_warning(s):
    echo(style(s, fg='bright_yellow'))