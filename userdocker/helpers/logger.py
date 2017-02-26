# -*- coding: utf-8 -*-

import logging

from ..config import *


logger = logging.getLogger('userdocker')


def logger_setup(args):
    logging.basicConfig()
    logging.root.setLevel(args.loglvl)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('global variables:')
        for _var in [
            'uid', 'user_name', 'gid', 'group_name',
            'gids', 'group_names',
            'user_home'
        ]:
            logger.debug("  %s = %r", _var, globals()[_var])

        logger.debug('configs loaded: %s\n', configs_loaded)
        logger.debug('resulting configs:')
        for _var, _val in list(globals().items()):
            if not _var.startswith('_') and _var.isupper():
                logger.debug("  %s = %r", _var, _val)
