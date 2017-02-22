# -*- coding: utf-8 -*-

EXECUTORS = {
    'docker': '/usr/bin/docker',
    'nvidia-docker': '/usr/bin/nvidia-docker',
}
DEFAULT_EXECUTOR = 'nvidia-docker'

VOLUME_MOUNTS = []
MOUNT_USER_HOME = True

USER_IN_CONTAINER = True

ENV_VARS = []
ENV_VARS_EXT = {
    'nvidia-docker': [
        'NCCL_TOPOLOGY=CUBEMESH',
    ]
}

# always injected
ARGS = [
    '--rm',
    '-t',
    '-i',
]
