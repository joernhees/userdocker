# -*- coding: utf-8 -*-

import logging
import os
import sys

from .helpers.logger import logger
from .helpers.logger import logger_setup

from .helpers.cmd import init_cmd
from .helpers.exceptions import UserDockerException
from .helpers.execute import exit_exec_cmd
from .parser import parse_args
from .subcommands import specific_command_executors


if not os.getenv('SUDO_UID'):
    logging.basicConfig()
    logger.warning("%s should be executed via sudo", sys.argv[0])


def prepare_and_exec_cmd(args):
    scmd = args.subcommand
    if scmd in specific_command_executors:
        specific_command_executors[scmd](args)
    else:
        exit_exec_cmd(init_cmd(args), dry_run=args.dry_run)


def parse_and_exec_cmd():
    if os.getenv('DOCKER_HOST'):
        raise UserDockerException(
            'ERROR: DOCKER_HOST env var not supported yet'
        )
    args = parse_args()
    logger_setup(args)
    prepare_and_exec_cmd(args)


def main():
    try:
        parse_and_exec_cmd()
    except UserDockerException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
