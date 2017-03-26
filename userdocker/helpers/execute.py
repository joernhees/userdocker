# -*- coding: utf-8 -*-

import logging
import os
from shlex import quote
import subprocess
import sys

from .exceptions import UserDockerException
from .logger import logger


def exec_cmd(cmd, dry_run=False, return_status=True, loglvl=logging.INFO):
    logger.log(
        loglvl,
        '%s command: %s',
        'would execute' if dry_run else 'executing',
        ' '.join([quote(c) for c in cmd])
    )
    logger.debug('internal repr: %s', cmd)

    if dry_run:
        return 0

    if not os.path.exists(cmd[0]):
        raise UserDockerException(
            "ERROR: can't find executable: %s" % cmd[0]
        )

    try:
        if return_status:
            ret = subprocess.check_call(cmd)
        else:
            ret = subprocess.check_output(cmd, universal_newlines=True)
        return ret
    except subprocess.CalledProcessError as e:
        ret = e.returncode
        sys.exit(ret)
