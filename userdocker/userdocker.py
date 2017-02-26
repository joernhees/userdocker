# -*- coding: utf-8 -*-

import logging
import os
import sys

from .commandline import prepare_commandline
from .execute import exec_cmd
from .helpers.logger import logger
from .helpers.logger import logger_setup
from .helpers.exceptions import UserDockerException
from .parser import parse_args


if not os.getenv('SUDO_UID'):
    logging.basicConfig()
    logger.warning("%s should be executed via sudo", sys.argv[0])


def parse_and_build_commandline():
    args = parse_args()
    logger_setup(args)
    cmd = prepare_commandline(args)
    return args, cmd


def main():
    try:
        args, cmd = parse_and_build_commandline()
        exec_cmd(cmd, args)
    except UserDockerException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
