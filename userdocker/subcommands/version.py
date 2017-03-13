# -*- coding: utf-8 -*-

from .. import __version__
from ..helpers.cmd import init_cmd


def prepare_commandline_version(args):
    print("Userdocker Version: %s" % __version__)
    return init_cmd(args)
