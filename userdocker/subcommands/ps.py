# -*- coding: utf-8 -*-
from ..helpers.cmd import init_cmd
from ..helpers.execute import exit_exec_cmd
from ..helpers.nvidia import nvidia_get_available_gpus
from ..helpers.nvidia import nvidia_get_gpus_used_by_containers
from ..helpers.parser import init_subcommand_parser


def parser_ps(parser):
    """Create parser for the ps subcommand.

    In addition to the arguments known from ``docker ps``, the userdocker ps
    subbcommand additionally supports the arguments ``--gpu-used``,
    ``--gpu-used-mine``, and ``gpu-free``. See the help for further
    information.
    """
    sub_parser = init_subcommand_parser(parser, 'ps')

    arg_group = sub_parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        "--gpu-used",
        help="show GPUs used by nvidia-docker containers",
        action="store_true",
    )

    arg_group.add_argument(
        "--gpu-used-mine",
        help="show GPUs reserved by your containers",
        action="store_true",
    )

    arg_group.add_argument(
        "--gpu-free",
        help="show allowed and free GPUs (asc by MB mem used)",
        action="store_true",
    )


def exec_cmd_ps(args):
    """Execute the ps subcommand."""
    if not args.gpu_used and not args.gpu_free and not args.gpu_used_mine:
        exit_exec_cmd(init_cmd(args), dry_run=args.dry_run)

    if args.gpu_used:
        gpus_used = nvidia_get_gpus_used_by_containers(args.executor_path)
        if gpus_used:
            print("\t".join(("GPU", "Container", "ContainerName", "User")))
        for i, l in sorted(gpus_used.items()):
            for container, container_name, user, _ in sorted(l):
                print("\t".join((str(i), container, container_name, user)))
    elif args.gpu_used_mine:
        available_gpus, own_gpus = nvidia_get_available_gpus(args.executor_path)
        for gpu in own_gpus:
            print(gpu)
    elif args.gpu_free:
        available_gpus, own_gpus = nvidia_get_available_gpus(args.executor_path)
        for gpu in available_gpus:
            print(gpu)
