# -*- coding: utf-8 -*-

from ..helpers.cmd import init_cmd
from ..helpers.execute import exec_cmd
from ..helpers.parser import init_subcommand_parser


def parser_pull(parser):
    sub_parser = init_subcommand_parser(parser, 'pull')

    sub_parser.add_argument(
        "name_tag_digest",
        help="NAME[:TAG|@DIGEST] to pull",
    )


def exec_cmd_pull(args):
    cmd = init_cmd(args)
    if args.name_tag_digest:
        cmd.append("--")
        cmd.append(args.name_tag_digest)
    exec_cmd(cmd, dry_run=args.dry_run)
