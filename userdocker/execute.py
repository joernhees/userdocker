# -*- coding: utf-8 -*-

import os
import subprocess
import sys

from .helpers.exceptions import UserDockerException
from .helpers.logger import logger


def exec_cmd(cmd, args, return_status=True):
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
        if return_status:
            ret = subprocess.check_call(cmd)
        else:
            ret = subprocess.check_output(cmd)
        return ret
    except subprocess.CalledProcessError as e:
        ret = e.returncode
        sys.exit(ret)
