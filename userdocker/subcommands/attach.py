# -*- coding: utf-8 -*-

import json
import logging

from ..config import uid
from ..helpers.cmd import init_cmd
from ..helpers.exceptions import UserDockerException
from ..helpers.execute import exit_exec_cmd
from ..helpers.logger import logger
from ..helpers.parser import init_subcommand_parser


def parser_attach(parser):
    sub_parser = init_subcommand_parser(parser, 'attach')

    sub_parser.add_argument(
        "--detach-keys",
        help="Override the key sequence for detaching a container",
    )

    sub_parser.add_argument(
        "container",
        help="container's ID or name to attach to"
    )


def exec_cmd_attach(args):
    cmd = init_cmd(args)

    if args.detach_keys:
        cmd += ['--detach-keys', args.detach_keys]

    container = args.container
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
            'ERROR: container %s was started by %d, but you are %d. Permission '
            'denied!' % (container, userdocker_uid, uid)
        )

    exit_exec_cmd(cmd, dry_run=args.dry_run)
