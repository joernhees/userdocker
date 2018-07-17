
import argparse

from ..helpers.cmd import init_cmd
from ..helpers.execute import exit_exec_cmd
from ..helpers.owner import check_container_owner
from ..helpers.parser import init_subcommand_parser


def parser_exec(parser):
    """Create parser for the exec subcommand."""
    sub_parser = init_subcommand_parser(parser, 'exec')

    sub_parser.add_argument(
        "container",
        help="container's ID or name to exec in"
    )

    sub_parser.add_argument(
        "exec_cmd",
        help="command to be executed in the container",
        nargs=argparse.REMAINDER
    )


def exec_cmd_exec(args):
    """Execute the exec subcommand.

    A check is performed to make sure that users can only exec in containers
    they own.
    """
    cmd = init_cmd(args)

    container = args.container
    cmd += [container]

    cmd.extend(args.exec_cmd)

    # check if we're allowed to exec in container (if it's ours)
    check_container_owner(container, args)

    exit_exec_cmd(cmd, dry_run=args.dry_run)
