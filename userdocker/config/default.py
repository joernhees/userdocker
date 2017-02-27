# -*- coding: utf-8 -*-

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
    # 'load',  # see RUN_PULL as well
    'ps',
    # 'pull',  # see RUN_PULL as well
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
