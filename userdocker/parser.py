# -*- coding: utf-8 -*-

import argparse
import logging
import sys

from . import __doc__
from . import __version__
from .config import ALLOWED_SUBCOMMANDS
from .config import EXECUTOR_DEFAULT
from .config import EXECUTORS
from .config import LOGLVL
from .helpers.parser import init_subcommand_parser

# dispatch specific specific_parsers to those defined in subcommands package
from .subcommands import specific_parsers


def parse_args():
    kwds = {
        "description": __doc__.strip(),
        "formatter_class": argparse.ArgumentDefaultsHelpFormatter,
    }
    if sys.version_info > (3, 5):
        kwds['allow_abbrev'] = False
    parser = argparse.ArgumentParser(**kwds)

    parser.add_argument(
        "--version",
        action="version",
        version='%(prog)s ' + __version__
    )

    debug_group = parser.add_mutually_exclusive_group()
    debug_group.add_argument(
        "-q", "--quiet",
        help="silences userdocker output below WARNING severity",
        action="store_const",
        dest="loglvl",
        const=logging.WARNING,
        default=LOGLVL,
    )
    debug_group.add_argument(
        "--debug",
        help="debug and config output for invoked docker command",
        action="store_const",
        dest="loglvl",
        const=logging.DEBUG,
        default=LOGLVL,
    )

    parser.add_argument(
        "-n", "--dry-run",
        help="doesn't actually invoke the docker command",
        action="store_true",
    )

    parser.add_argument(
        "--executor",
        help="prints the invoked docker commandline",
        default=EXECUTOR_DEFAULT,
        choices=EXECUTORS,
    )

    # individual commands will be sub-specific_parsers
    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    for scmd in ALLOWED_SUBCOMMANDS:
        specific_parser = specific_parsers.get(scmd)
        if specific_parser:
            specific_parser(subparsers)
        else:
            init_subcommand_parser(subparsers, scmd)

    args = parser.parse_args()
    args.executor_path = EXECUTORS[args.executor]
    return args
