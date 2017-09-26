# -*- coding: utf-8 -*-

import argparse
import logging
import os
import re

from .. import __version__
from ..config import ALLOWED_IMAGE_REGEXPS
from ..config import CAPS_ADD
from ..config import CAPS_DROP
from ..config import ENV_VARS
from ..config import ENV_VARS_EXT
from ..config import NV_ALLOWED_GPUS
from ..config import NV_DEFAULT_GPU_COUNT_RESERVATION
from ..config import NV_MAX_GPU_COUNT_RESERVATION
from ..config import PROBE_USED_MOUNTS
from ..config import RUN_PULL
from ..config import USER_IN_CONTAINER
from ..config import VOLUME_MOUNTS_ALWAYS
from ..config import VOLUME_MOUNTS_AVAILABLE
from ..config import VOLUME_MOUNTS_DEFAULT
from ..config import gid
from ..config import uid
from ..config import user_name
from ..helpers.cmd import init_cmd
from ..helpers.exceptions import UserDockerException
from ..helpers.execute import exec_cmd
from ..helpers.execute import exit_exec_cmd
from ..helpers.logger import logger
from ..helpers.nvidia import nvidia_get_available_gpus
from ..helpers.parser import init_subcommand_parser


def parser_run(parser):
    sub_parser = init_subcommand_parser(parser, 'run')

    sub_parser.add_argument(
        "--no-default-mounts",
        help="does not automatically add default mounts",
        action="store_true",
    )

    if VOLUME_MOUNTS_ALWAYS or VOLUME_MOUNTS_AVAILABLE or VOLUME_MOUNTS_DEFAULT:
        sub_parser.add_argument(
            "-v", "--volume",
            help="user specified volume mounts (can be given multiple times)",
            action="append",
            dest="volumes",
            default=[],
        )

    sub_parser.add_argument(
        "--entrypoint",
        help="Overwrite the default ENTRYPOINT of the image",
    )

    sub_parser.add_argument(
        "-w", "--workdir",
        help="Working directory inside the container",
    )

    sub_parser.add_argument(
        "image",
        help="the image to run",
    )

    sub_parser.add_argument(
        "image_args",
        help="arguments passed to the image",
        nargs=argparse.REMAINDER
    )


def prepare_nvidia_docker_run(args):
    # mainly handles GPU arbitration via ENV var for nvidia-docker
    # note that these are ENV vars for the command, not the container

    if os.getenv('NV_HOST'):
        raise UserDockerException('ERROR: NV_HOST env var not supported yet')

    # check if allowed
    if not NV_ALLOWED_GPUS:
        raise UserDockerException(
            "ERROR: No GPUs available due to admin setting."
        )

    nv_gpus = os.getenv('NV_GPU', '')
    if nv_gpus:
        # the user has set NV_GPU, just check if it's ok
        nv_gpus = [g.strip() for g in nv_gpus.split(',')]
        try:
            nv_gpus = [int(gpu) for gpu in nv_gpus]
        except ValueError as e:
            raise UserDockerException(
                "ERROR: Can't parse NV_GPU, use index notation: %s" % e
            )

        if not (
                NV_ALLOWED_GPUS == 'ALL'
                or all(gpu in NV_ALLOWED_GPUS for gpu in nv_gpus)):
            raise UserDockerException(
                "ERROR: Access to at least one specified NV_GPU denied by "
                "admin. Available GPUs: %r" % (NV_ALLOWED_GPUS,)
            )

        # check if in bounds (and MAX >= 0)
        if 0 <= NV_MAX_GPU_COUNT_RESERVATION < len(nv_gpus):
            raise UserDockerException(
                "ERROR: Number of requested GPUs > %d (admin limit)" % (
                    NV_MAX_GPU_COUNT_RESERVATION,)
            )

        # check if available
        gpus_available = nvidia_get_available_gpus(args.executor_path)
        for g in nv_gpus:
            if g not in gpus_available:
                raise UserDockerException(
                    'ERROR: GPU %d is currently not available!\nUse:\n'
                    '"sudo userdocker ps --gpu-free" to find available GPUs.\n'
                    '"sudo userdocker ps --gpu-used" and "nvidia-smi" to see '
                    'status.' % g
                )
    else:
        # NV_GPU wasn't set, use admin defaults, tell user
        gpu_default = NV_DEFAULT_GPU_COUNT_RESERVATION
        logger.info(
            "NV_GPU environment variable not set, trying to acquire admin "
            "default of %d GPUs" % gpu_default
        )
        gpus_available = nvidia_get_available_gpus(args.executor_path)
        gpus = gpus_available[:gpu_default]
        if len(gpus) < gpu_default:
            raise UserDockerException(
                'Could not find %d available GPU(s)!\nUse:\n'
                '"sudo userdocker ps --gpu-used" and "nvidia-smi" to see '
                'status.' % gpu_default
            )
        gpu_env = ",".join([str(g) for g in gpus])
        logger.info("Setting NV_GPU=%s" % gpu_env)
        os.environ['NV_GPU'] = gpu_env


def exec_cmd_run(args):
    cmd = init_cmd(args)

    mounts = []
    mounts_available = \
        VOLUME_MOUNTS_ALWAYS + VOLUME_MOUNTS_DEFAULT + VOLUME_MOUNTS_AVAILABLE

    mounts += VOLUME_MOUNTS_ALWAYS

    if not args.no_default_mounts:
        mounts += VOLUME_MOUNTS_DEFAULT

    for user_mount in args.volumes:
        if user_mount in mounts:
            continue
        if user_mount in mounts_available:
            mounts += [user_mount]
            continue

        # literal matches didn't work, allow potential unspecified
        # container_path mounts
        host_path = user_mount.split(':')[0]
        if host_path in mounts:
            continue
        if user_mount in mounts_available:
            mounts += [user_mount]
            continue

        # check if the user appended a 'ro' flag
        if len(user_mount.split(':')) == 3:
            host_path, container_path, flag = user_mount.split(':')
            if flag == 'ro':
                st = ':'.join([host_path, container_path])
                if st in mounts:
                    # upgrade mount to include ro flag
                    idx = mounts.index(st)
                    mounts[idx] = user_mount
                    continue
                if st in mounts_available:
                    mounts += [user_mount]

        raise UserDockerException(
            "ERROR: given mount not allowed: %s" % user_mount
        )

    mount_host_paths = [m.split(':')[0] for m in mounts]
    for ms in mount_host_paths:
        if not os.path.exists(ms):
            raise UserDockerException(
                "ERROR: mount can't be found: %s" % ms
            )
        if PROBE_USED_MOUNTS and os.path.isdir(ms):
            os.listdir(ms)

    for mount in mounts:
        cmd += ["-v", mount]


    if args.executor == 'nvidia-docker':
        prepare_nvidia_docker_run(args)

    env_vars = ENV_VARS + ENV_VARS_EXT.get(args.executor, [])
    env_vars += [
        "USERDOCKER=%s" % __version__,
        "USERDOCKER_USER=%s" % user_name,
        "USERDOCKER_UID=%d" % uid,
    ]
    for env_var in env_vars:
        cmd += ['-e', env_var]


    if USER_IN_CONTAINER:
        cmd += ["-u", "%d:%d" % (uid, gid)]

    for cap_drop in CAPS_DROP:
        cmd += ["--cap-drop=%s" % cap_drop]
    for cap_add in CAPS_ADD:
        cmd += ["--cap-add=%s" % cap_add]

    if args.workdir:
        cmd += ["-w", args.workdir]
    if args.entrypoint:
        cmd += ["--entrypoint", args.entrypoint]

    # additional injection protection, deactivated for now due to nvidia-docker
    # unability to handle this
    # cmd.append("--")

    img = args.image
    if ":" not in img and "@" not in img:
        # user didn't explicitly set a tag or digest, append ":latest"
        img += ":latest"

    if ALLOWED_IMAGE_REGEXPS:
        for air in ALLOWED_IMAGE_REGEXPS:
            if re.match(air, img):
                break
        else:
            raise UserDockerException(
                "ERROR: image %s not in allowed image regexps: %s" % (
                    img, ALLOWED_IMAGE_REGEXPS))

    # pull image?
    if RUN_PULL == "default":
        # just let `docker run` do its thing
        pass
    elif RUN_PULL == "always":
        # pull image
        exec_cmd(
            [args.executor_path, 'pull', img],
            dry_run=args.dry_run,
            loglvl=logging.DEBUG,
        )
    elif RUN_PULL == "never":
        # check if image is available locally
        tmp = exec_cmd(
            [args.executor_path, 'images', '-q', img],
            return_status=False,
            loglvl=logging.DEBUG,
        )
        if not tmp:
            raise UserDockerException(
                "ERROR: you can only use locally available images, but %s could"
                " not be found locally" % img
            )
    else:
        raise UserDockerException(
            "ERROR: RUN_PULL config variable not expected range, contact admin"
        )

    cmd.append(img)
    cmd.extend(args.image_args)

    exit_exec_cmd(cmd, dry_run=args.dry_run)
