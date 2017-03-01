# -*- coding: utf-8 -*-

################################################################################
# WARNING:
# /etc/userdocker/default.py will not be loaded at runtime, but is meant as a
# template! It will be overwritten by future installs/updates!
# Copy this file to /etc/docker/config.py, then edit!
#
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
# - package defaults
# - /etc/userdocker/group.py
# - /etc/userdocker/group/config_50_udocker.py
# - /etc/userdocker/group/config_99_adm.py
# - ...
# This means that config_99_adm.py can grant users in group adm a lot more
# permissions (reliably), even if they are also in the udocker group.
################################################################################

# Admin default value for userdocker log level:
# ['DEBUG', 'INFO', 'WARNING', 'ERROR']
LOGLVL = 'INFO'

# Available executors for users.
EXECUTORS = {
    'docker': '/usr/bin/docker',
    'nvidia-docker': '/usr/bin/nvidia-docker',
}
EXECUTOR_DEFAULT = 'docker'

# The following allows you to specify which docker top level commands a user can
# run at all (still restricted by the following settings):
ALLOWED_SUBCOMMANDS = [
    'dockviz',  # tree visualization of images
    'images',
    'load',  # see RUN_PULL as well
    'ps',
    'pull',  # see RUN_PULL as well
    'run',
    'version',
]

# Arguments (more precisely simple flags) that you want to make available to the
# user or enforce. Do not include args that are handled below (e.g. run -v)!
# The following arguments will always be injected for the corresponding command:
ARGS_ALWAYS = {
    'run': [
        # '-t',
        # '-i',
        '--rm',
    ],
}
# The following arguments are available to the user for the given command:
# (aliases are supported as tuples below, but not in ARGS_ALWAYS)
ARGS_AVAILABLE = {
    'images': [
        ('-a', '--all'),
        '--digests',
        '--no-trunc',
        ('-q', '--quiet'),
    ],
    'load': [
        ('-q', '--quiet'),
    ],
    'ps': [
        ('-a', '--all'),
        ('-l', '--latest'),
        ('-s', '--size'),
        ('-q', '--quiet'),
        '--no-trunc',
    ],
    'pull': [
        ('-a', '--all-tags'),
    ],
    'run': [
        ('-t', '--tty'),
        ('-i', '--interactive'),
        '--read-only',
    ],
}


# Volume mounts:
# - VOLUME_MOUNTS_ALWAYS will be mounted whether the user wants it or not
# - VOLUME_MOUNTS_AVAILABLE will only be mounted if the user explicitly
#   specifies them
# - VOLUME_MOUNTS_DEFAULT will be added unless the user specifies the
#   --no-default-mounts option
# - The user can mount any of the above explicitly with "-v", redundancy is ok
# - You (admin) can use "{USER}" and "{HOME}" vars in mount specs
# - You (admin) can specify whatever usually comes after the "-v" arg in
#   "host_path:container_path:flags" form. If you do not specify a target, the
#   user may select one, which is potentially unsafe. If you don't specify a
#   flag, the user can append a "ro" to guard herself (even for
#   VOLUME_MOUNTS_ALWAYS).
# Example:
# VOLUME_MOUNTS_DEFAULT = ["/netscratch:/netscratch", "/data:/input:ro"]
VOLUME_MOUNTS_ALWAYS = []
VOLUME_MOUNTS_AVAILABLE = []
VOLUME_MOUNTS_DEFAULT = [
    # default mount user home
    "{HOME}:{HOME}",
]

# This setting issues a listdir for used host dirs in mounts.
# Useful for server-side auto-mounts.
PROBE_USED_MOUNTS = True


# User is allowed to run an image if any of the following regexps match it
ALLOWED_IMAGE_REGEXPS = [
    '^[A-Za-z_].*',
]

# Normally docker run automatically pulls images that aren't available locally.
# This possible values here are ['default', 'never', 'always']
# 'never' will restrict to locally available images (see ALLOWED_COMMANDS and
# restrict load command if desired!).
RUN_PULL = 'default'


# If set, the user will run with his uid and gid in the container.
# Changing this to false is probably a really bad idea, especially when combined
# with any mounts.
USER_IN_CONTAINER = True

# The following allows to drop / grant capabilities of all containers.
# By default we drop all and make the
CAPS_DROP = ['ALL']
CAPS_ADD = []
PRIVILEGED = False

# User ability to publish ports
# The ALLOWED_PUBLISH_PORTS_ALL allows the user to use the -P flag, which
# publishes all ports that are EXPOSEd in the container to random host ports
# (non priv range).
# Notice that by default such ports are world accessible, so in case you want to
# protect them, make sure to have (a docker compatible) iptables in place.
ALLOWED_PUBLISH_PORTS_ALL = True

# Environment vars to set for the container:
ENV_VARS = []
ENV_VARS_EXT = {
    'nvidia-docker': [
        'NCCL_TOPOLOGY=CUBEMESH',
    ]
}

# By default userdocker will set USERDOCKER and USERDOCKER_USER ENV vars to the
# container. They might in future be used to allow users to interact with their
# previously started containers.
ENV_VARS_SET_USERDOCKER_META_INFO = True
