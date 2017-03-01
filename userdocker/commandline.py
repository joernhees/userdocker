# -*- coding: utf-8 -*-

from .helpers.cmd import init_cmd

# dispatch specific command preparation to those defined in subcommands package
from .subcommands import specific_commandline_preparers


def prepare_commandline(args):
    scmd = args.subcommand
    prep_cmdline = specific_commandline_preparers.get(scmd, init_cmd)
    return prep_cmdline(args)
