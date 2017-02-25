#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""
This is a wrapper to allow restricted access to the docker command to users.

Feedback welcome:
https://github.com/joernhees/userdocker
"""

import argparse
import os
import pwd
import re
import subprocess
import sys

from config import *


__version__ = '1.0.0-dev'


class UserDockerException(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__.strip(),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    debug_group = parser.add_mutually_exclusive_group()
    debug_group.add_argument(
        "-q", "--quiet",
        help="silences output of invoked docker command",
        action="store_true",
        default=QUIET,
    )

    debug_group.add_argument(
        "--debug",
        help="even more output for invoked docker command",
        action="store_true",
        default=DEBUG,
    )

    parser.add_argument(
        "-n", "--dry-run",
        help="doesn't actually invoke the docker command",
        action="store_true",
    )

    parser.add_argument(
        "--executor",
        help="prints the invoked docker commandline",
        default=EXECUTOR_DEFAULT,
        choices=EXECUTORS,
    )

    # individual commands will be sub-parsers
    subparsers = parser.add_subparsers(dest='cmd')
    subparsers.required = True

    ############################################################################
    # parser for docker run
    ############################################################################
    parser_run = subparsers.add_parser(
        'run',
        help='lets a user run a "docker run"',
    )
    parser_run.set_defaults(prepare_commandline=prepare_commandline_run)

    parser_run.add_argument(
        "--no-default-mounts",
        help="does not automatically add default mounts",
        action="store_true",
    )

    parser_run.add_argument(
        "-v", "--volume",
        help="user specified volume mounts (can be given multiple times)",
        action="append",
        dest='volumes',
        default=[],
    )

    parser_run.add_argument(
        "image",
        help="the image to run",
    )

    parser_run.add_argument(
        "image_args",
        help="arguments passed to the image",
        nargs=argparse.REMAINDER
    )

    ############################################################################
    # parser for docker ps
    ############################################################################
    parser_ps = subparsers.add_parser(
        'ps',
        help='lets a user run a "docker ps"',
    )
    parser_ps.set_defaults(prepare_commandline=prepare_commandline_ps)


    args = parser.parse_args()
    args.executor_path = EXECUTORS[args.executor]
    return args


def expand_mounts(mounts, **kwds):
    return [m.format(**kwds) for m in mounts]


def prepare_commandline_run(args):
    uid = os.getuid()
    uid = int(os.getenv('SUDO_UID', uid))
    gid = os.getgid()
    gid = int(os.getenv('SUDO_GID', gid))
    user_name = pwd.getpwuid(uid)[0]
    user_home = pwd.getpwuid(uid)[5]
    mt_args = {'USERNAME': user_name, 'HOME': user_home}

    cmd = [args.executor_path, 'run'] + ARGS_RUN

    mounts = []
    mounts_always = expand_mounts(VOLUME_MOUNTS_ALWAYS, **mt_args)
    mounts_default = expand_mounts(VOLUME_MOUNTS_DEFAULT, **mt_args)
    mounts_available = mounts_always + mounts_default + \
        expand_mounts(VOLUME_MOUNTS_AVAILABLE, **mt_args)

    mounts += mounts_always

    if not args.no_default_mounts:
        mounts += expand_mounts(VOLUME_MOUNTS_DEFAULT, **mt_args)

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
        cmd += ['-v', mount]

    env_vars = ENV_VARS + ENV_VARS_EXT.get(args.executor_path, [])
    if ENV_VARS_SET_USERDOCKER_META_INFO:
        env_vars += [
            'USERDOCKER=%s' % __version__,
            'USERDOCKER_USER=%s' % user_name,
            'USERDOCKER_UID=%d' % uid,
        ]
    for env_var in env_vars:
        cmd += ['-e', env_var]


    if USER_IN_CONTAINER:
        cmd += ['-u', '%d:%d' % (uid, gid)]

    for cap_drop in CAPS_DROP:
        cmd += ['--drop-cap=%s' % cap_drop]
    for cap_add in CAPS_ADD:
        cmd += ['--add-cap=%s' % cap_add]
    if PRIVILEGED:
        cmd += ['--privileged']

    cmd.append('--')

    img = args.image
    if ALLOWED_IMAGE_REGEXPS:
        for air in ALLOWED_IMAGE_REGEXPS:
            if re.match(air, img):
                break
        else:
            raise UserDockerException(
                "ERROR: image not in allowed images: %s" % img
            )

    # pull image?
    if RUN_PULL == 'default':
        # just let `docker run` do its thing
        pass
    elif RUN_PULL == 'always':
        # pull image
        exec_cmd([args.executor_path, 'pull', img], args)
    elif RUN_PULL == 'never':
        # check if image is available locally
        tmp = subprocess.check_output([args.executor_path, 'images', '-q', img])
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


def prepare_commandline_ps(args):
    cmd = [args.executor_path, 'ps'] + ARGS_PS
    return cmd


def exec_cmd(cmd, args):
    if not args.quiet:
        print(
            'would execute' if args.dry_run else 'executing',
            'command:',
            ' '.join(cmd)
        )
    if args.debug:
        print('internal repr:', cmd)

    if args.dry_run:
        return 0

    if not os.path.exists(cmd[0]):
        raise UserDockerException(
            "ERROR: can't find docker executable: %s" % cmd[0]
        )

    try:
        ret = subprocess.check_call(
            cmd,
        )
    except subprocess.CalledProcessError as e:
        ret = e.returncode
        sys.exit(ret)
    return ret


def main():
    try:
        args = parse_args()
        cmd = args.prepare_commandline(args)
        exec_cmd(cmd, args)
    except UserDockerException as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
