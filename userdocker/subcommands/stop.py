# -*- coding: utf-8 -*-

import argparse

from ..helpers.cmd import init_cmd
from ..helpers.execute import exit_exec_cmd
from ..helpers.owner import check_container_owner
from ..helpers.parser import init_subcommand_parser


def parser_stop(parser):
    """Create parser for the stop subcommand."""
    sub_parser = init_subcommand_parser(parser, 'stop')

    sub_parser.add_argument(
        "containers",
        help="one or more container IDs or names to stop",
        nargs=argparse.REMAINDER
    )


def exec_cmd_stop(args):
    """Execute the stop subcommand.

    A check is performed to make sure that users can only stop containers they
    own.
    """
    cmd = init_cmd(args)

    for container in args.containers:
        cmd += [container]
        # check if we're allowed to stop container (if it's ours)
        check_container_owner(container, args)

    exit_exec_cmd(cmd, dry_run=args.dry_run)
