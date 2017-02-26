# -*- coding: utf-8 -*-


def prepare_commandline_dockviz(args):
    # just run dockviz
    return [
        args.executor_path, "run", "-it", "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "nate/dockviz", "images", "--tree"
    ]
