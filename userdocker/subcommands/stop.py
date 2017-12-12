# -*- coding: utf-8 -*-

from ..helpers.cmd import init_cmd
from ..helpers.execute import exit_exec_cmd
from ..helpers.owner import check_container_owner
from ..helpers.parser import init_subcommand_parser

def parser_stop(parser):
    sub_parser = init_subcommand_parser(parser, 'stop')

    sub_parser.add_argument(
        "container",
        help="container's ID or name to stop"
    )


def exec_cmd_stop(args):
    cmd = init_cmd(args)

    container = args.container
    cmd += [container]

    # check if we're allowed to stop container (if it's ours)
    check_container_owner(container, args)

    exit_exec_cmd(cmd, dry_run=args.dry_run)
