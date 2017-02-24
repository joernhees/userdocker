# -*- coding: utf-8 -*-

EXECUTORS = {
    'docker': '/usr/bin/docker',
    'nvidia-docker': '/usr/bin/nvidia-docker',
}
DEFAULT_EXECUTOR = 'docker'


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
    '.*',
]

# Normally docker run automatically pulls images that aren't available locally.
# This possible values here are ['default', 'never', 'always']
# 'never' will restrict to locally available images.
RUN_PULL = 'default'


# If set, the user will run with his uid and gid in the container.
# Changing this to false is probably a really bad idea, especially when combined
# with any mounts.
USER_IN_CONTAINER = True

# Environment vars to set for the container:
ENV_VARS = []
ENV_VARS_EXT = {
    'nvidia-docker': [
        'NCCL_TOPOLOGY=CUBEMESH',
    ]
}

# always injected
ARGS_RUN = [
    '--rm',
    '-t',
    '-i',
]
ARGS_PS = ['-a']
