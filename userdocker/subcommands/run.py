# -*- coding: utf-8 -*-

import argparse
import os
import re

from .. import __version__
from ..config import ALLOWED_PUBLISH_PORTS_ALL
from ..config import ALLOWED_IMAGE_REGEXPS
from ..config import CAPS_ADD
from ..config import CAPS_DROP
from ..config import ENV_VARS
from ..config import ENV_VARS_EXT
from ..config import ENV_VARS_SET_USERDOCKER_META_INFO
from ..config import PRIVILEGED
from ..config import PROBE_USED_MOUNTS
from ..config import RUN_PULL
from ..config import USER_IN_CONTAINER
from ..config import VOLUME_MOUNTS_ALWAYS
from ..config import VOLUME_MOUNTS_AVAILABLE
from ..config import VOLUME_MOUNTS_DEFAULT
from ..config import gid
from ..config import uid
from ..config import user_home
from ..config import user_name
from ..execute import exec_cmd
from ..helpers.cmd import init_cmd
from ..helpers.exceptions import UserDockerException
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

    if ALLOWED_PUBLISH_PORTS_ALL:
        sub_parser.add_argument(
            "-P", "--publish-all",
            help="Publish all exposed ports to random ports",
            action="store_true",
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


def render_mounts(mounts, **kwds):
    return [m.format(**kwds) for m in mounts]


def prepare_commandline_run(args):
    mt_args = {"USERNAME": user_name, "HOME": user_home}

    cmd = init_cmd(args)

    mounts = []
    mounts_always = render_mounts(VOLUME_MOUNTS_ALWAYS, **mt_args)
    mounts_default = render_mounts(VOLUME_MOUNTS_DEFAULT, **mt_args)
    mounts_available = mounts_always + mounts_default + \
        render_mounts(VOLUME_MOUNTS_AVAILABLE, **mt_args)

    mounts += mounts_always

    if not args.no_default_mounts:
        mounts += render_mounts(VOLUME_MOUNTS_DEFAULT, **mt_args)

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

    if args.publish_all:
        cmd += ["-P"]

    env_vars = ENV_VARS + ENV_VARS_EXT.get(args.executor, [])
    if ENV_VARS_SET_USERDOCKER_META_INFO:
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
    if PRIVILEGED:
        cmd += ["--privileged"]

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
        exec_cmd([args.executor_path, 'pull', img], args)
    elif RUN_PULL == "never":
        # check if image is available locally
        tmp = exec_cmd(
            [args.executor_path, 'images', '-q', img],
            args,
            return_status=False
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

    return cmd
