# -*- coding: utf-8 -*-

################################################################################
# WARNING:
# /etc/userdocker/default.py will not be loaded at runtime, but is meant as a
# template! It will be overwritten by future installs/updates!
# Copy this file to /etc/docker/config.py, then edit!
#
# The following (python) variables may be used throughout config files (see
# VOLUME_MOUNTS_DEFAULT or ENV_VARS for an example):
from . import uid, gid, user_name, group_name, user_home
# (if you like, you can remove the line without any effect)
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
#
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
    'attach',  # allows users to re-attach to _their_ containers
    'dockviz',  # tree visualization of images
    'images',
    'load',  # see RUN_PULL as well
    'ps',
    'pull',  # see RUN_PULL as well
    'run',
    'stop',
    'version',
]

# Arguments:
# Arguments can be specified in four different ways:
# 1) As a short argument (flag): '-f'
# 2) As a long argument (flag): '--flag'
# 3) As a short argument with a value: '-f value' or '-f=value' or '-f="value"'
# 3) As a long argument with a value: '--flag=value' or '--flag value' or
#    '--flag="value"'
#
# Use an empty value (e.g. '-f=') to allow all possible values for the given
# argument.
#
# These can be combined in lists or tuples as follows:
# 1) As a combination of one or more short and long options: ['--flag', '-f']
# 2) As a combination of one or more long options with values:
#   ['--flag=val1', '--flag="val2 val3"']
# Note that for these lists/tuples, only the _first_ argument will be used to
# determine what to pass on to the executor, so make sure to put aliases last:
#   ['--real-flag', '--alias']
# When specifying several values for an argument, it is not necessary to repeat
# the argument each time (it is possible to add aliases though):
#   ['--flag=val', '=val2', '=val3 val4'], or
#   ['--flag=val', '--alias1=val2', '--alias2=val3 val4']
#
# When specifying arguments via ARGS_ALWAYS or ARGS_DEFAULT, always use the
# 'real flag', i.e. the first flag listed in the corresponding entry in
# ARGS_AVAILABLE, or else these arguments will be passed on twice and an error
# will be thrown by the executor.

# Arguments that you want to enforce on the user:
# Do not include args that are handled below (e.g. run -v)!
# See explanation above on how to specify arguments.
# Combinations as tuples / lists are not supported here.
# The following arguments will always be injected for the corresponding
# subcommand:
ARGS_ALWAYS = {
    'run': [
        # '--example=value with spaces',
        # '-i',
        # '-t',
        '--rm',
    ],
}

# These arguments will be passed to the executor unless the user overrides them
# with one of the available values in ARGS_AVAILABLE or disables default
# arguments using the --no-default-args switch.
# For flags, this acts much like ARGS_ALWAYS unless the user disables default
# args completely.
# Combinations as tuples / lists are not supported here.
ARGS_DEFAULT = {

}

# The following arguments (without options) are available to the user for the
# given command.
# Do not include args that are handled below (e.g. run -v)!
# See explanation above on how to specify arguments.
# Combinations are supported as tuples / lists here.
ARGS_AVAILABLE = {
    'attach': [
        '--no-stdin',
    ],
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
        # users can map all exposed container ports to random free host ports:
        ('-P', '--publish-all'),
        # workdir and entrypoint can be chosen freely
        ('--workdir=', '-w'),
        '--entrypoint=',
    ],
}


# Volume mounts:
# - VOLUME_MOUNTS_ALWAYS will be mounted whether the user wants it or not
# - VOLUME_MOUNTS_AVAILABLE will only be mounted if the user explicitly
#   specifies them
# - VOLUME_MOUNTS_DEFAULT will be added unless the user specifies the
#   --no-default-mounts option
# - The user can mount any of the above explicitly with "-v", redundancy is ok
# - You (admin) can specify whatever usually comes after the "-v" arg in
#   "host_path:container_path:flags" form. If you do not specify a target, the
#   user may select one, which is potentially unsafe. If you don't specify a
#   flag, the user can append a "ro" to guard herself (even for
#   VOLUME_MOUNTS_ALWAYS).
# Example:
# VOLUME_MOUNTS_DEFAULT = ['/netscratch:/netscratch', '/data:/input:ro']
VOLUME_MOUNTS_ALWAYS = []
VOLUME_MOUNTS_AVAILABLE = []
VOLUME_MOUNTS_DEFAULT = [
    # Mount /etc/{passwd,groups} for correct uid,gid display in containers.
    # Not enabling this has mostly cosmetic effects. All mappings to the host
    # file system are via uid:gid.
    # WARNING: not enabled by default, as systems using ldap usually do not
    # offer the necessary information in these files, but via getent.
    # '/etc/passwd:/etc/passwd:ro',
    # '/etc/group:/etc/group:ro',

    # default mount user's home
    user_home + ':' + user_home,
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
# By default we drop all
CAPS_DROP = ['ALL']
CAPS_ADD = []

# User ability to map ports explicitly:
# Unlike the probably safe `-P` run arg (which maps all exposed container ports
# to random free host ports (world accessible)), giving users explicit control
# over port mappings is probably not the best idea, as they are likely to
# collide on frequently used ports such as 5000 or 8080.
# Also it might unintentionally allow them to bind ports in the root range if
# you are not careful.
# For flexibility, we allow you to specify regexps that each -p arg is matched
# against one by one. Only if each of the user's -p args matches at least one of
# these, the docker run command is executed. If the list is empty, the -p
# argument is neither allowed nor shown to the user.
ALLOWED_PORT_MAPPINGS = [
    # useful defaults: most similar to -P, but allows users to select
    # ports instead of mapping all exposed publicly. Also might allow them to
    # bind them local to host only:
    r'^127\.0\.0\.1::[0-9]+$',  # local access from host (via random free port)
    '^[0-9]+$',  # public access (via random free host port)

    # more examples:

    # allow `-p 127.0.0.1:5000-6000:80`, so user can map container 80 to
    # random host port in range of 5000-6000 that is only accessible from host:
    # r'^127\.0\.0\.1:5000-6000:80$'

    # allow `-p 8080:80`, so user can map container 80 to host 8080 (if free):
    # '^8080:80$'  # probably useful in user-specific configs

    # allow all (probably bad idea!):
    # '^.*$',  # allows all, probably bad idea!
]

# Environment vars to set for the container:
ENV_VARS = [
    # sets HOME env var to user's home
    'HOME=' + user_home,
]
ENV_VARS_EXT = {
    'nvidia-docker': [
        'NCCL_TOPOLOGY=CUBEMESH',
    ]
}


# nvidia docker specific settings
# The following settings allow to restrict the way users can use nvidia GPUs
# in their container.
# - NV_ALLOWED_GPUS allows you to only make a subset of GPUs available to users.
#   Setting this to [] or None will result in nvidia-docker to always fail as no
#   GPUs are available. If that's desired, you should instead remove the
#   nvidia-docker executor above, as that's less confusing for users!
# - NV_DEFAULT_GPU_COUNT_RESERVATION allows to specify how many GPUs are passed
#   to a container if the user does not specify the NV_GPU env var. This is
#   different from the nvidia-docker defaults, which would by default allow
#   access to all GPUs!
# - NV_MAX_GPU_COUNT_RESERVATION allows you to limit the amount of GPUs made
#   available to a single container. Setting this to -1 means no limit.
# - GPUs on which more than NV_GPU_UNAVAILABLE_ABOVE_MEMORY_USED MB of memory is
#   used will be marked as unavailable. This setting is userdocker independent.
#   Setting this to -1 results in GPUs always being regarded as available.
# - If NV_EXCLUSIVE_GPU_RESERVATION is set, any GPUs already used in any other
#   container are regarded as unavailable for this container.
# - NV_ALLOW_OWN_GPU_REUSE allows users to run multiple containers on GPUs they
#   already use. This only happens when explicitly setting NV_GPU.
NVIDIA_SMI = '/usr/bin/nvidia-smi'  # path to nvidia-smi
NV_ALLOWED_GPUS = 'ALL'  # otherwise a list like [1, 3]. [] for none.
NV_DEFAULT_GPU_COUNT_RESERVATION = 1
NV_MAX_GPU_COUNT_RESERVATION = -1
NV_GPU_UNAVAILABLE_ABOVE_MEMORY_USED = 0
NV_EXCLUSIVE_CONTAINER_GPU_RESERVATION = True
NV_ALLOW_OWN_GPU_REUSE = True
