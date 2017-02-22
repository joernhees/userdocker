#! /usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import pwd
import subprocess
import sys

from config import *


def parse_args():
    parser = argparse.ArgumentParser(
        description='allows restricted access to docker for users',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--quiet",
        help="silences output of invoked docker command",
        action="store_true",
    )

    parser.add_argument(
        "--dry-run",
        help="doesn't actually invoke the docker command",
        action="store_true",
    )

    parser.add_argument(
        "--executor",
        help="prints the invoked docker commandline",
        action="store",
        default=DEFAULT_EXECUTOR,
        type=str,
        choices=EXECUTORS,
    )

    parser.add_argument(
        "image",
        help="the image to run",
        action="store",
        type=str,
    )

    parser.add_argument(
        "image_args",
        help="arguments passed to the image",
        action="store",
        type=str,
        nargs=argparse.REMAINDER
    )

    return parser.parse_args()


def build_docker_commandline(args):
    uid = os.getuid()
    uid = int(os.getenv('SUDO_UID', uid))
    gid = os.getgid()
    gid = int(os.getenv('SUDO_GID', gid))
    # user_name = pwd.getpwuid(uid)[0]
    user_home = pwd.getpwuid(uid)[5]

    cmd = [args.executor]
    cmd += ARGS

    for volume_mount in VOLUME_MOUNTS:
        cmd += ['-v', volume_mount]

    if MOUNT_USER_HOME:
        cmd += ['-v', '%s:%s' % (user_home, user_home)]

    for env_var in ENV_VARS + ENV_VARS_EXT.get(args.executor, []):
        cmd += ['-e', env_var]

    if USER_IN_CONTAINER:
        cmd += ['-u', '%d:%d' % (uid, gid)]

    cmd.append('--')
    cmd.append(args.image)
    cmd.extend(args.image_args)

    return cmd


def main():
    args = parse_args()
    cmd = build_docker_commandline(args)

    if not args.quiet:
        print(cmd)

    if not args.dry_run:
        sys.exit(subprocess.check_call(
            cmd,
        ))


if __name__ == '__main__':
    main()
