# -*- coding: utf-8 -*-

from .dockviz import *
from .images import *
from .pull import *
from .run import *

SPECIFIC_PARSER_PREFIX = 'parser_'
specific_parsers = {
    _var.split(SPECIFIC_PARSER_PREFIX)[1]: _val
    for _var, _val in globals().items()
    if _var.startswith(SPECIFIC_PARSER_PREFIX)
}

SPECIFIC_COMMANDLINE_PREPARER_PREFIX = 'prepare_commandline_'
specific_commandline_preparers = {
    _var.split(SPECIFIC_COMMANDLINE_PREPARER_PREFIX)[1]: _val
    for _var, _val in globals().items()
    if _var.startswith(SPECIFIC_COMMANDLINE_PREPARER_PREFIX)
}

__all__ = [specific_parsers, specific_commandline_preparers]
