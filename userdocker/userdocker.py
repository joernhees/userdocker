#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""
This is a wrapper to allow restricted access to the docker command to users.

Feedback welcome:
https://github.com/joernhees/userdocker
"""

import argparse
from glob import glob
import grp
import os
import pwd
import re
import subprocess
import sys
import logging

__version__ = '1.0.0-dev'


logger = logging.getLogger('userdocker')

if not os.getenv('SUDO_UID'):
    logging.basicConfig()
    logger.warning("%s should be executed via sudo", sys.argv[0])
uid = os.getuid()
uid = int(os.getenv('SUDO_UID', uid))
gid = os.getgid()
gid = int(os.getenv('SUDO_GID', gid))
user_pwd = pwd.getpwuid(uid)
user_name = user_pwd.pw_name
user_home = user_pwd.pw_dir
group_name = grp.getgrgid(gid).gr_name
group_names, gids = zip(*[
    (_g.gr_name, _g.gr_gid)
    for _g in grp.getgrall()
    if user_name in _g.gr_mem
])
del user_pwd


# The order of config files is (if existing):
# - package defaults
# - /etc/userdocker/config.py
# - /etc/userdocker/group/config_<prio>_<group_name>.py (see note below)
# - /etc/userdocker/gid/config_<prio>_<gid>.py (see note below)
# - /etc/userdocker/user/config_<user_name>.py
# - /etc/userdocker/uid/config_<uid>.py
#
# All config files are executed in place, allowing later config files to
# override or modify previous ones. The above might sound complicated, but just
# start with a /etc/userdocker/config.py and then define exceptions later.
#
# As a user can be in several groups, the group configs include a 2 digit prio.
# On execution, we will get all groups for the user, collect the corresponding
# config files matching those groups if they exist and load all collected
# config files sorted ascending by prio. Lowest prio is 00 (loaded first),
# highest prio is 99 (loaded last).
# Afterwards the same is done for gid config files.

# Example: if a user is in groups "adm" and "udocker" and an admin created the
# config files config_99_adm.py and config_50_udocker.py, then the execution
# order is:
# - /etc/userdocker/group.py
# - /etc/userdocker/group/config_50_udocker.py
# - /etc/userdocker/group/config_99_adm.py
# - ...
# This means that config_99_adm.py can grant users in group adm a lot more
# permissions (reliably), even if they are also in the udocker group.

from config import *
configs_loaded = ['default']
_cd = '/etc/userdocker/'
_cfns = (
    glob(_cd + 'config.py')
    + sorted([
        _cfn for _gn in group_names
             for _cfn in glob(_cd + 'group/config_[0-9][0-9]_%s.py' % _gn)])
    + sorted([
        _cfn for _gid in gids
             for _cfn in glob(_cd + 'gid/config_[0-9][0-9]_%d.py' % _gid)])
    + glob(_cd + 'user/config_%s.py' % user_name)
    + glob(_cd + 'uid/config_%d.py' % uid)
)
for _cfn in _cfns:
    with open(_cfn) as _cf:
        exec(_cf.read())
        configs_loaded.append(_cfn)


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
        help="silences userdocker output below WARNING severity",
        action="store_const",
        dest="loglvl",
        const=logging.WARNING,
        default=LOGLVL,
    )
    debug_group.add_argument(
        "--debug",
        help="debug and config output for invoked docker command",
        action="store_const",
        dest="loglvl",
        const=logging.DEBUG,
        default=LOGLVL,
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
    subparsers = parser.add_subparsers(dest="scmd")
    subparsers.required = True

    for scmd in ALLOWED_SUBCOMMANDS:
        add_parser = globals().get("add_parser_%s" % scmd)
        if add_parser:
            add_parser(subparsers)
        else:
            init_subcommand_parser(subparsers, scmd)

    args = parser.parse_args()
    args.executor_path = EXECUTORS[args.executor]
    return args


def init_subcommand_parser(parent_parser, scmd):
    parser = parent_parser.add_parser(
        scmd,
        help='Lets a user run "docker %s ..." command' % scmd
    )
    prepare_commandline_f = globals().get(
        "prepare_commandline_%s" % scmd,
        init_cmd
    )
    parser.set_defaults(
        prepare_commandline=prepare_commandline_f,
        patch_through_args=[],
    )

    # patch args through
    _args_seen = []
    for arg in ARGS_AVAILABLE.get(scmd, []) + ARGS_ALWAYS.get(scmd, []):
        if isinstance(arg, str):
            args = [arg]
        elif isinstance(arg, (list, tuple, set)):
            args = list(arg)
        else:
            raise NotImplementedError(
                "Cannot understand admin defined ARG %s for command %s" % (
                    arg, scmd))

        # remove dups (e.g. from being in AVAILABLE and ALWAYS)
        args = [arg for arg in args if arg not in _args_seen]
        _args_seen.extend(args)

        # make sure arg starts with - and doesn't contain = or ' '
        for arg in args:
            if not arg.startswith('-') or '=' in arg or ' ' in arg:
                raise NotImplementedError(
                    "Cannot understand admin defined ARG %s for command %s" % (
                        arg, scmd))

        h = "see docker help"
        if set(args) & set(ARGS_ALWAYS.get(scmd, [])):
            h += ' (enforced by admin)'
        parser.add_argument(
            *args,
            help=h,
            action="append_const",
            const=args[0],
            dest="patch_through_args",
        )
    return parser


def add_parser_run(parser):
    parser_run = init_subcommand_parser(parser, 'run')

    parser_run.add_argument(
        "--no-default-mounts",
        help="does not automatically add default mounts",
        action="store_true",
    )

    if VOLUME_MOUNTS_ALWAYS or VOLUME_MOUNTS_AVAILABLE or VOLUME_MOUNTS_DEFAULT:
        parser_run.add_argument(
            "-v", "--volume",
            help="user specified volume mounts (can be given multiple times)",
            action="append",
            dest="volumes",
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


def init_cmd(args):
    cmd = [args.executor_path, args.scmd] + ARGS_ALWAYS.get(args.scmd, [])
    logger.debug("patch_through_args: %s", args.patch_through_args)
    for pt_arg in args.patch_through_args:
        if pt_arg not in cmd:
            cmd.append(pt_arg)
    return cmd


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

    env_vars = ENV_VARS + ENV_VARS_EXT.get(args.executor_path, [])
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
        cmd += ["--drop-cap=%s" % cap_drop]
    for cap_add in CAPS_ADD:
        cmd += ["--add-cap=%s" % cap_add]
    if PRIVILEGED:
        cmd += ["--privileged"]

    cmd.append("--")

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
    if RUN_PULL == "default":
        # just let `docker run` do its thing
        pass
    elif RUN_PULL == "always":
        # pull image
        exec_cmd([args.executor_path, 'pull', img], args)
    elif RUN_PULL == "never":
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


def exec_cmd(cmd, args):
    logger.info(
        '%s command: %s',
        'would execute' if args.dry_run else 'executing',
        ' '.join(cmd)
    )
    logger.debug('internal repr: %s', cmd)

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


def logger_setup(args):
    logging.basicConfig()
    logging.root.setLevel(args.loglvl)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('global variables:')
        for _var in [
            'uid', 'user_name', 'gid', 'group_name',
            'gids', 'group_names',
            'user_home'
        ]:
            logger.debug("  %s = %r", _var, globals()[_var])

        logger.debug('configs loaded: %s\n', configs_loaded)
        logger.debug('resulting configs:')
        for _var, _val in list(globals().items()):
            if not _var.startswith('_') and _var.isupper():
                logger.debug("  %s = %r", _var, _val)


def main():
    try:
        args = parse_args()
        logger_setup(args)
        cmd = args.prepare_commandline(args)
        exec_cmd(cmd, args)
    except UserDockerException as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
