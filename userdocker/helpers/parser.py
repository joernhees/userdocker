# -*- coding: utf-8 -*-

import argparse
import re
from typing import Tuple

from ..config import ARGS_ALWAYS, ARGS_AVAILABLE, ARGS_DEFAULT
from .exceptions import UserDockerException


def init_subcommand_parser(parent_parser: argparse._SubParsersAction, scmd: str) -> argparse.ArgumentParser:
    """Initialize subcommand parser.

    Args:
        parent_parser: The parent parser, handling global arguments.
        scmd: The subcommand for which a parser is being initialized.

    Returns:
        Initialized subcommand parser.
    """
    parser = parent_parser.add_parser(
        scmd,
        help='Lets a user run "docker %s ..." command' % scmd,
    )
    parser.set_defaults(
        patch_through_args=[],
    )

    # patch args through
    _args_seen = []
    for args in ARGS_AVAILABLE.get(scmd, []) + ARGS_ALWAYS.get(scmd, []) \
            + ARGS_DEFAULT.get(scmd, []):
        if isinstance(args, str):
            # just a single arg or arg=value as string
            args = [args]
        elif isinstance(args, (list, tuple)):
            # aliases or several arg=value entries as list or tuple
            args = list(args)
        else:
            raise NotImplementedError(
                "Cannot understand admin defined ARG %s for command %s" % (
                    args, scmd))

        # only argument names, not values
        simple_args = []
        for arg_and_value in args:
            # make sure arg starts with -
            if not arg_and_value.startswith('-') and not arg_and_value.startswith('='):
                raise NotImplementedError(
                    "Cannot understand admin defined ARG %s for command %s" % (
                        arg_and_value, scmd))

            arg = split_into_arg_and_value(arg_and_value)[0]

            # skip on empty or known arguments
            if arg is '' or arg in _args_seen:
                continue

            if ' ' in arg:
                raise NotImplementedError(
                    "Cannot understand admin defined ARG %s for command %s" % (
                        arg_and_value, scmd))

            simple_args.append(arg)

        # skip if all args were already known or empty
        if not simple_args:
            continue

        _args_seen.extend(simple_args)

        h = "see docker help"
        if set(args) & set(ARGS_ALWAYS.get(scmd, [])):
            h += ' (enforced by admin)'
        kwds = {
            "help": h,
            "action": PatchThroughAction,
            "const": args,
        }
        parser.add_argument(*set(simple_args), **kwds)

    return parser


def split_into_arg_and_value(arg_and_value: str) -> Tuple[str, str]:
    """Splits the given string into argument and value.

    Possible values for ``arg_and_value``:
    - ``'-f'`` or ``'--flag'`` (results in ``('-f', None)`` and
        ``('--flag', None)``, respectively)
    - ``'--flag val'`` or ``'--flag=val'`` or ``'--flag "val"'`` or
        ``'--flag="val"'``, all of which result in ``('--flag', 'val')``

    Args:
        arg_and_value: Argument and value.

    Returns:
        Tuple containing the argument and the value (or ``None`` if no value is
        present).

    """

    arg = arg_and_value
    value = None

    if '=' in arg_and_value:
        arg, value = arg_and_value.split('=', 1)
    elif ' ' in arg_and_value:
        arg, value = arg_and_value.split(' ', 1)

    return arg.strip(), (strip_surrounding_quotes(value) if value is not None else value)


def strip_surrounding_quotes(string: str) -> str:
    """Strip surrounding quotes from string.

    This function removes whitespaces as well as single and double quotes at
    the beginning and end of the string.
    """
    pattern = re.compile('["\']+(.*)["\']+')
    value_parsed = string.strip()

    match = pattern.match(value_parsed)

    return value_parsed if not match else match.group(1)


def join_arg_and_value(arg: str, value: str) -> str:
    """Join the argument and value.

    Joins the given argument and and value with an equal sign (``'='``) or
    simply returns the argument if the value is ``None``.
    """
    return arg + '=' + value if value is not None else arg


class PatchThroughAction(argparse.Action):
    """Parser action for arguments patched through to the executor.

    Attributes:
        DEST (str): Name of the entry for the patch-through arguments in the
            argparse namespace.
    """
    DEST = "patch_through_args"

    def __init__(self, option_strings, dest, const, nargs=None, **kwargs):
        """Extract the argument and values of the parser action."""

        # nargs will be determined automatically
        if nargs is not None:
            raise ValueError("nargs not allowed")

        self.args = const
        self.arg = None
        self.values = []

        for arg_and_value in self.args:
            arg, value = split_into_arg_and_value(arg_and_value)

            if self.arg is None and arg is not '':
                self.arg = arg

            # Collect allowed argument values
            if value is not None:
                self.values.append(value)

        if self.arg is None:
            raise ValueError("No arg found for values {}".format(self.values))

        nargs = 1 if len(self.values) > 0 else 0

        super(PatchThroughAction, self).__init__(
            option_strings=option_strings, nargs=nargs,
            dest=dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """Validate the given values and store argument in namespace.

        Raises:
            UserDockerException: If more than one value or an invalid value has
                been specified.
        """

        if len(values) > 1:
            raise UserDockerException(
                "Parameters with more than one argument not supported for argument {}"
                    .format(self.arg))
        if len(values) > 0 and not ("" in self.values or values[0] in self.values):
            raise UserDockerException(
                "Value {} for parameter {} not allowed (allowed values: {})"
                    .format(values, self.arg, self.values))

        arg = (self.arg + '=' + values[0].strip()) if len(values) > 0 else self.arg

        patch_through_args = list(getattr(namespace, self.DEST, []))
        patch_through_args.append(arg)
        setattr(namespace, self.DEST, patch_through_args)
