# -*- coding: utf-8 -*-

import logging

from ..helpers.cmd import init_cmd
from ..helpers.execute import exit_exec_cmd
from ..helpers.logger import logger
from ..helpers.owner import check_container_owner
from ..helpers.parser import init_subcommand_parser

def parser_attach(parser):
    """Create parser for the attach subcommand."""
    sub_parser = init_subcommand_parser(parser, 'attach')

    sub_parser.add_argument(
        "--detach-keys",
        help="Override the key sequence for detaching a container",
    )

    sub_parser.add_argument(
        "container",
        help="container's ID or name to attach to"
    )


def exec_cmd_attach(args):
    """Execute the attach subcommand.

    A check is performed to make sure that users can only attach to containers
    they own.
    """
    cmd = init_cmd(args)

    if args.detach_keys:
        cmd += ['--detach-keys', args.detach_keys]

    container = args.container
    cmd += [container]

    # check if we're allowed to attach to container (if it's ours)
    check_container_owner(container, args)

    logger.info("Press enter if the shell does not appear")

    exit_exec_cmd(cmd, dry_run=args.dry_run)
