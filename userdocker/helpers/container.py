# -*- coding: utf-8 -*-

import json
import logging
import re
from typing import Tuple

from ..config import user_name
from .execute import exec_cmd


def container_find_userdocker_user_uid(container_env: dict) -> Tuple[str, int]:
    """Find and return userdocker username and user ID for the given container.

    Args:
        container_env: Container environment variables.

    Returns:
        The username (or '') and user ID (or None) of the userdocker user.
    """
    pairs = [var.partition('=') for var in container_env]
    users = [v for k, _, v in pairs if k == 'USERDOCKER_USER']
    uids = [v for k, _, v in pairs if k == 'USERDOCKER_UID']
    return users[0] if users else '', int(uids[0]) if uids else None


def container_get_next_name(docker: str):
    """Return the default name of the next container for the user.

    Default container names are `$user_$i`, where $i is a unique number. The
    most recently started container always has the highest number."""

    running_containers = container_get_running(docker)

    if not running_containers:
        return user_name + "_1"

    running_containers_names = exec_cmd(
        [
            docker, 'inspect', '--format', '[{{json .Name}}]'
        ] + running_containers,
        return_status=False,
        loglvl=logging.DEBUG,
    )

    container_name_re = re.compile('^/' + user_name + '_([0-9]+)$')
    container_index = 0
    for line in running_containers_names.splitlines():
        container_names = json.loads(line)

        for name in container_names:
            m = container_name_re.match(name)
            if m:
                container_index = max(container_index, int(m.groups()[0]))

    return user_name + '_' + str(container_index + 1)


def container_get_running(docker: str) -> list:
    """Return a list of running containers."""

    running_containers = exec_cmd(
        [docker, 'ps', '-q'],
        return_status=False,
        loglvl=logging.DEBUG,
    ).split()

    return running_containers