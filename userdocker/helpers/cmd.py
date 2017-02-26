# -*- coding: utf-8 -*-

from .logger import logger
from ..config import ARGS_ALWAYS


def init_cmd(args):
    cmd = [args.executor_path, args.scmd] + ARGS_ALWAYS.get(args.scmd, [])
    logger.debug("patch_through_args: %s", args.patch_through_args)
    for pt_arg in args.patch_through_args:
        if pt_arg not in cmd:
            cmd.append(pt_arg)
    return cmd
