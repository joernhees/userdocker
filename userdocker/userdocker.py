# -*- coding: utf-8 -*-

"""
This is a wrapper to allow restricted access to the docker command to users.

Feedback welcome:
https://github.com/joernhees/userdocker
"""
print('load main userdocker script')
import argparse
import logging
import os
import sys

from .config import LOGLVL
from .config import EXECUTORS
from .config import EXECUTOR_DEFAULT
from .config import ALLOWED_SUBCOMMANDS
from .helpers.logger import logger
from .helpers.logger import logger_setup
from .helpers.parser import init_subcommand_parser
from .helpers.exceptions import UserDockerException
from .helpers.cmd import exec_cmd

# make all parsers and command line preparers for subcommands available
from .subcommands import *


if not os.getenv('SUDO_UID'):
    logging.basicConfig()
    logger.warning("%s should be executed via sudo", sys.argv[0])


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__.strip(),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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

    # individual commands will be sub-parsers
    subparsers = parser.add_subparsers(dest="scmd")
    subparsers.required = True

    for scmd in ALLOWED_SUBCOMMANDS:
        add_parser = globals().get("add_parser_%s" % scmd)
        if add_parser:
            add_parser(subparsers)
        else:
            init_subcommand_parser(subparsers, scmd)

    args = parser.parse_args()
    args.executor_path = EXECUTORS[args.executor]
    return args


def prepare_commandline(args):
    scmd = args.scmd
    prepare_commandline_scmd = globals().get(
        "prepare_commandline_%s" % scmd,
        init_cmd
    )
    return prepare_commandline_scmd(args)


def main():
    try:
        args = parse_args()
        logger_setup(args)
        cmd = prepare_commandline(args)
        exec_cmd(cmd, args)
    except UserDockerException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
