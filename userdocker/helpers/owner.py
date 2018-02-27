# -*- coding: utf-8 -*-

import json
import logging

from ..config import uid
from ..helpers.exceptions import UserDockerException
from ..helpers.execute import exec_cmd
from ..helpers.logger import logger

def check_container_owner(container: str, args) -> None:
    """Check if the user is allowed to interact with the container.

    Users are allowed to interact with containers they own (i.e. have started).

    Args:
        container: Name or ID of the container.
        args (argparse.Namespace): Command arguments.

    Raises:
        UserDockerException: If the given container was not started by
            ``userdocker`` or the container is owned by another user.
    """

    container_env = exec_cmd(
        [
            args.executor_path, 'inspect',
            '--format', '{{json .Config.Env}}',
            container
        ],
        return_status=False,
        loglvl=logging.DEBUG,
    )
    if not container_env:
        raise UserDockerException(
            'ERROR: could not find container %s' % container
        )
    userdocker_uid_env = [
        env for env in json.loads(container_env)
        if env.startswith('USERDOCKER_UID')
    ]
    if not userdocker_uid_env:
        raise UserDockerException(
            'ERROR: could not find USERDOCKER_UID env var in container %s'
            % container
        )
    userdocker_uid = int(userdocker_uid_env[0].split('USERDOCKER_UID=')[1])
    logger.debug(
        "Container %s was started by user id %d", container, userdocker_uid)
    if uid != userdocker_uid:
        raise UserDockerException(
            'ERROR: container %s was started by user id %d, but you are %d. '
            'Permission denied!' % (container, userdocker_uid, uid)
        )
