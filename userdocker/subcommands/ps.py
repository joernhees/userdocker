# -*- coding: utf-8 -*-
from ..helpers.cmd import init_cmd
from ..helpers.execute import exec_cmd
from ..helpers.nvidia import nvidia_get_available_gpus
from ..helpers.nvidia import nvidia_get_gpus_used_by_containers
from ..helpers.parser import init_subcommand_parser


def parser_ps(parser):
    sub_parser = init_subcommand_parser(parser, 'ps')

    arg_group = sub_parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        "--gpu-reservations",
        help="show userdocker reserved GPUs",
        action="store_true",
    )

    arg_group.add_argument(
        "--gpu-free",
        help="show allowed free GPUs",
        action="store_true",
    )


def exec_cmd_ps(args):
    if not args.gpu_reservations and not args.gpu_free:
        exec_cmd(init_cmd(args), dry_run=args.dry_run)

    gpus_used = nvidia_get_gpus_used_by_containers(args.executor_path)
    if args.gpu_reservations:
        for i, (container, container_name, user) in sorted(gpus_used.items()):
            print("\t".join((i, container, container_name, user)))
    elif args.gpu_free:
        available_gpus = nvidia_get_available_gpus(args.executor_path)
        for gpu in available_gpus:
            print(gpu)
