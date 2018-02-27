# -*- coding: utf-8 -*-

import logging

from .. import config

logger = logging.getLogger('userdocker')


def logger_setup(args) -> None:
    """Set up logging and print loaded config."""
    logging.basicConfig()
    logging.root.setLevel(args.loglvl)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug('configs loaded: %s', config.configs_loaded)
        if len(config.configs_loaded) <= 1:
            logger.warning(
                'No config found, using defaults! You should copy\n%s\nto\n%s\n'
                'and adapt the setting to your needs!',
                config.path(), '/etc/userdocker/config.py'
            )
        logger.debug('resulting config:')
        for _var, _val in config.items():
            logger.debug("  %s = %r", _var, _val)
