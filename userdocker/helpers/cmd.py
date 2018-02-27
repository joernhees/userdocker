# -*- coding: utf-8 -*-

from ..config import ARGS_ALWAYS, ARGS_DEFAULT
from .logger import logger
from .parser import split_into_arg_and_value, join_arg_and_value


def init_cmd(args) -> list:
    """Initialize the command.

    The command is built using
    - executor and subcommand,
    - ARGS_ALWAYS,
    - user arguments,
    - ARGS_DEFAULT if the user did not disable default arguments.

    Later arguments to not overwrite earlier arguments.

    Args:
        args (argparse.Namespace): Collected user arguments as well as executor
            / subcommand.

    Returns:
        The initialized command.
    """
    cmd = [args.executor_path, args.subcommand]
    logger.debug("patch_through_args: %s", args.patch_through_args)

    cmd = append_args(cmd, ARGS_ALWAYS.get(args.subcommand, []), True)
    cmd = append_args(cmd, args.patch_through_args)

    if not args.no_default_args:
        cmd = append_args(cmd, ARGS_DEFAULT.get(args.subcommand, []), True)

    return cmd


def append_args(cmd: list, args: list, parsed: bool=False) -> list:
    """Append the given arguments to the given command.

    Existing arguments will not be overwritten.

    Args:
        cmd: The command as a list of arguments.
        args: The arguments to be appended.
        parsed: Whether the arguments should be parsed. This is necessary
            only for arguments which came from the configuration, since user
            arguments are parsed by the shell.

    Returns:
        The command including the appended arguments.
    """
    for arg_and_value in args:
        # when checking for existing arguments, ignore values
        arg, value = split_into_arg_and_value(arg_and_value)

        append = True

        # ignore the first two entries of the list (executor and subcommand)
        for cmd_arg in cmd[2:]:
            # if the argument already exists in the command, skip
            if cmd_arg.startswith(arg):
                append = False
                break

        if append:
            cmd.append(arg_and_value if not parsed else join_arg_and_value(arg, value))

    return cmd
