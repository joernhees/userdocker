# -*- coding: utf-8 -*-

import logging
import os
from shlex import quote
import subprocess
import sys

from .exceptions import UserDockerException
from .logger import logger


def exec_cmd(cmd: list, dry_run: bool=False, return_status: bool=True, loglvl: int=logging.INFO):
    """Execute the given command.

    Args:
        cmd: The command as a list of arguments.
        dry_run: If true, the command will not be executed but only printed.
        return_status: Whether to return the status code of the command.
        loglvl: Log level to be used during the invocation of the command.

    Returns:
        The command output or status code, depending on ``return_status``.

    Raises:
        UserDockerException: If the executor can't be found.
    """
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


def exit_exec_cmd(cmd: list, dry_run: bool=False) -> None:
    """Execute the given command and exit."""
    sys.exit(exec_cmd(cmd, dry_run=dry_run))
