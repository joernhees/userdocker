# -*- coding: utf-8 -*-

from ..helpers.execute import exit_exec_cmd


def exec_cmd_dockviz(args):
    """Runs the dockviz convenience subcommand.

    This subcommand is a shorthand for
    ``docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock nate/dockviz images --tree``
    """

    # just run dockviz
    cmd = [
        args.executor_path, "run", "-it", "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "nate/dockviz", "images", "--tree"
    ]
    exit_exec_cmd(cmd, dry_run=args.dry_run)
