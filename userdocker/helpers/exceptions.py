# -*- coding: utf-8 -*-


class UserDockerException(Exception):
    """Exception for user errors like invalid or forbidden arguments.

    Not to be used for internal or configuration errors.
    """
    pass
