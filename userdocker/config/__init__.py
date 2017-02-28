# -*- coding: utf-8 -*-

from glob import glob
import grp
import os
import pwd


# The order of config files is (if existing):
# - package defaults
# - /etc/userdocker/config.py
# - /etc/userdocker/group/config_<prio>_<group_name>.py (see note below)
# - /etc/userdocker/gid/config_<prio>_<gid>.py (see note below)
# - /etc/userdocker/user/config_<user_name>.py
# - /etc/userdocker/uid/config_<uid>.py
#
# All config files are executed in place, allowing later config files to
# override or modify previous ones. The above might sound complicated, but just
# start with a /etc/userdocker/config.py and then define exceptions later.
#
# As a user can be in several groups, the group configs include a 2 digit prio.
# On execution, we will get all groups for the user, collect the corresponding
# config files matching those groups if they exist and load all collected
# config files sorted ascending by prio. Lowest prio is 00 (loaded first),
# highest prio is 99 (loaded last).
# Afterwards the same is done for gid config files.

# Example: if a user is in groups "adm" and "udocker" and an admin created the
# config files config_99_adm.py and config_50_udocker.py, then the execution
# order is:
# - /etc/userdocker/group.py
# - /etc/userdocker/group/config_50_udocker.py
# - /etc/userdocker/group/config_99_adm.py
# - ...
# This means that config_99_adm.py can grant users in group adm a lot more
# permissions (reliably), even if they are also in the udocker group.


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
