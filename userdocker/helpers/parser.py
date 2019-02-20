# -*- coding: utf-8 -*-

import sys
import argparse

from ..config import ARGS_ALWAYS
from ..config import ARGS_AVAILABLE


class _PatchThroughAssignmentAction(argparse._AppendAction):
    """Action that appends not only the value but the option=value to dest.

    Useful for patch through args with assignment like: --shm-size=1g.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        super(_PatchThroughAssignmentAction, self).__call__(
            parser, namespace,
            values=option_string + '=' + values,
            option_string=option_string)


def init_subcommand_parser(parent_parser, scmd):
    parser = parent_parser.add_parser(
        scmd,
        help='Lets a user run "docker %s ..." command' % scmd,
    )
    parser.set_defaults(
        patch_through_args=[],
    )

    # patch args through
    _args_seen = []
    for args in ARGS_AVAILABLE.get(scmd, []) + ARGS_ALWAYS.get(scmd, []):
        if isinstance(args, str):
            # just a single arg as string
            args = [args]
        elif isinstance(args, (list, tuple)):
            # aliases as list or tuple
            args = list(args)
        else:
            raise NotImplementedError(
                "Cannot understand admin defined ARG %s for command %s" % (
                    args, scmd))

        # remove dups (e.g. from being in AVAILABLE and ALWAYS)
        args = [arg for arg in args if arg not in _args_seen]
        _args_seen.extend(args)
        if not args:
            continue

        for arg in args:
            # make sure each arg starts with - and doesn't contain ' '
            if not arg.startswith('-') or ' ' in arg:
                raise NotImplementedError(
                    "Cannot understand admin defined ARG %s for command %s" % (
                        arg, scmd))
            if '=' in arg:
                if len(args) != 1:
                    raise NotImplementedError(
                        "Only supports single string args with values: "
                        "%s for command %s" % (arg, scmd))

        h = "see docker help"
        if set(args) & set(ARGS_ALWAYS.get(scmd, [])):
            h += ' (enforced by admin)'

        s = args[0]
        if '=' in s:
            arg, val = s.split('=')
            args = [arg]
            kwds = {
                "help": h,
                "action": _PatchThroughAssignmentAction,
                "choices": [val],
                "dest": "patch_through_args",
            }
        else:
            kwds = {
                "help": h,
                "action": "append_const",
                "const": s,
                "dest": "patch_through_args",
            }
        parser.add_argument(*args, **kwds)

    return parser
