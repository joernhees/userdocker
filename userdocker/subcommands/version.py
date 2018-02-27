# -*- coding: utf-8 -*-

from .. import __version__
from ..helpers.cmd import init_cmd
from ..helpers.execute import exit_exec_cmd


def exec_cmd_version(args):
    """Execute the version subcommand.

    Before executing ``docker version``, this will print the userdocker
    version.
    """
    print("Userdocker Version: %s\n" % __version__)
    exit_exec_cmd(init_cmd(args), dry_run=args.dry_run)
