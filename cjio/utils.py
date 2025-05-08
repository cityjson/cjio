"""Various utility functions"""

import os.path
import click


def verify_filename(filename):
    """Verify if the provided output filename is a file or a directory"""
    res = {"dir": False, "path": ""}
    if os.path.isdir(filename):
        res["dir"] = True
        absp = os.path.abspath(filename)
        if os.path.exists(absp):
            res["path"] = absp
        else:
            raise click.ClickException("Couldn't expand %s to absolute path" % filename)
    else:
        base = os.path.basename(filename)
        dirname = os.path.abspath(os.path.dirname(filename))
        # parent directory must exist, we don't recurse further
        if not os.path.exists(dirname):
            raise click.ClickException('Path does not exist: "%s"' % (dirname))
        fname, extension = os.path.splitext(base)
        res["path"] = os.path.join(dirname, base)
        if len(extension) == 0:
            res["dir"] = True
        else:
            res["dir"] = False
    return res
