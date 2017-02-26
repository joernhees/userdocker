# -*- coding: utf-8 -*-

import os
import subprocess
import sys

from ..config import ARGS_ALWAYS
from .exceptions import UserDockerException
from .logger import logger


def init_cmd(args):
    cmd = [args.executor_path, args.scmd] + ARGS_ALWAYS.get(args.scmd, [])
    logger.debug("patch_through_args: %s", args.patch_through_args)
    for pt_arg in args.patch_through_args:
        if pt_arg not in cmd:
            cmd.append(pt_arg)
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
