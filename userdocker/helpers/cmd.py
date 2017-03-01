# -*- coding: utf-8 -*-

from ..config import ARGS_ALWAYS
from .logger import logger


def init_cmd(args):
    cmd = [args.executor_path, args.subcommand] \
          + ARGS_ALWAYS.get(args.subcommand, [])
    logger.debug("patch_through_args: %s", args.patch_through_args)
    for pt_arg in args.patch_through_args:
        if pt_arg not in cmd:
            cmd.append(pt_arg)
    return cmd
