# -*- coding: utf-8 -*-

from ..helpers.cmd import init_cmd
from ..helpers.parser import init_subcommand_parser


def parser_images(parser):
    sub_parser = init_subcommand_parser(parser, 'images')

    sub_parser.add_argument(
        "repo_tag",
        help="optional repo[:tag] to restrict output",
        nargs='?',
    )


def prepare_commandline_images(args):
    cmd = init_cmd(args)
    if args.repo_tag:
        cmd.append("--")
        cmd.append(args.repo_tag)
    return cmd
