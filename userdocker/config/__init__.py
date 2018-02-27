# -*- coding: utf-8 -*-

from glob import glob
import grp
import os
import pwd


uid = os.getuid()
uid = int(os.getenv('SUDO_UID', uid))
gid = os.getgid()
gid = int(os.getenv('SUDO_GID', gid))
user_pwd = pwd.getpwuid(uid)
user_name = user_pwd.pw_name
user_home = user_pwd.pw_dir
group_name = grp.getgrgid(gid).gr_name
group_names = []
gids = []
for _g in grp.getgrall():
    if user_name in _g.gr_mem:
        group_names.append(_g.gr_name)
        gids.append(_g.gr_gid)
del user_pwd


# see default.py for explanation on config load order
from .default import *
configs_loaded = ['default']
_cd = '/etc/userdocker/'
_cfns = (
    glob(_cd + 'config.py')
    + sorted([
        _cfn for _gn in group_names
             for _cfn in glob(_cd + 'group/config_[0-9][0-9]_%s.py' % _gn)])
    + sorted([
        _cfn for _gid in gids
             for _cfn in glob(_cd + 'gid/config_[0-9][0-9]_%d.py' % _gid)])
    + glob(_cd + 'user/config_%s.py' % user_name)
    + glob(_cd + 'uid/config_%d.py' % uid)
)
for _cfn in _cfns:
    with open(_cfn) as _cf:
        exec(_cf.read())
        configs_loaded.append(_cfn)


# helpers to show final config
def items():
    """Return configuration items."""
    masked = (
        # imports:
        'default', 'glob', 'grp', 'os', 'pwd',
        # methods:
        'items', 'path',
    )
    for _var, _val in sorted(globals().items()):
        if not _var.startswith('_') and _var not in masked:
            yield _var, _val


def path():
    """Return the config file path."""
    return os.path.dirname(os.path.realpath(__file__))
