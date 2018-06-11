# -*- coding: utf-8 -*-

import json
import logging
import re
from collections import defaultdict
from typing import Tuple

from ..config import uid, NVIDIA_SMI, NV_ALLOWED_GPUS, \
    NV_EXCLUSIVE_CONTAINER_GPU_RESERVATION, \
    NV_GPU_UNAVAILABLE_ABOVE_MEMORY_USED
from .logger import logger
from .execute import exec_cmd
from .container import container_get_running, container_find_userdocker_user_uid


def nvidia_get_gpus_used_by_containers(docker: str) -> defaultdict:
    """Return the GPUs currently used by docker containers.

    Args:
        docker: Path of the docker executor.

    Returns:
        ``defaultdict`` mapping GPU IDs to a list
            ``(container, container_name, container_user, container_uid)``
    """

    running_containers = container_get_running(docker)

    gpu_used_by_containers = defaultdict(list)

    if not running_containers:
        return gpu_used_by_containers

    gpu_used_by_containers_str = exec_cmd(
        [
            docker, 'inspect', '--format',
            '[{{json .Name}}, {{json .Id}}, {{json .Config.Env}}, '
            '{{json $.HostConfig.Devices}}]'
        ] + running_containers,
        return_status=False,
        loglvl=logging.DEBUG,
    )
    logger.debug('gpu_used_by_containers_str: %s', gpu_used_by_containers_str)

    gpu_dev_id_re = re.compile('^/dev/nvidia([0-9]+)$')
    for line in gpu_used_by_containers_str.splitlines():
        container_name, container, container_env, devs = json.loads(line)

        # Skip of no devs found
        if devs is None:
            continue

        for dev in devs:
            d = dev.get('PathOnHost', '')
            m = gpu_dev_id_re.match(d)
            if m:
                gpu_id = int(m.groups()[0])
                container_user, container_uid = container_find_userdocker_user_uid(container_env)
                gpu_used_by_containers[gpu_id].append(
                    (container, container_name, container_user, container_uid)
                )
                logger.debug(
                    'gpu %d used by container: %s, name: %s, user: %s, uid: %s',
                    gpu_id, container, container_name, container_user, container_uid
                )
    return gpu_used_by_containers


def nvidia_get_available_gpus(docker: str, nvidia_smi: str=NVIDIA_SMI) -> Tuple[list, list]:
    """Return the available GPUs.

    Availability of GPUs depends on:
    - ``NV_ALLOWED_GPUS``: GPUs not in this list are generally not available
    - ``NV_GPU_UNAVAILABLE_ABOVE_MEMORY_USED``: if more than this amount of memory
            is used, a GPU is considered unavailable
    - ``NV_EXCLUSIVE_CONTAINER_GPU_RESERVATION``: if ``True``, GPUs used by other
            containers are considered unavailable

    See the configuration file for additional details.
    """
    if not NV_ALLOWED_GPUS:
        return list(), list()

    gpu_mem_used_str = exec_cmd(
        [nvidia_smi,
         '--query-gpu=index,memory.used,utilization.gpu',
         '--format=csv'],
        return_status=False,
        loglvl=logging.DEBUG,
    )
    logger.debug('gpu usage:\n%s', gpu_mem_used_str)
    gpu_mem_used = {}
    for line in gpu_mem_used_str.splitlines()[1:]:  # skip header
        gpu, mem_used, gpu_utilization = line.split(', ')
        gpu = int(gpu)
        mem_used = int(mem_used.split(' MiB')[0])
        gpu_mem_used[gpu] = mem_used

    gpus_used_by_containers = nvidia_get_gpus_used_by_containers(docker)
    gpus_used_by_own_containers = [
        gpu for gpu, info in gpus_used_by_containers.items()
        if any(i[3] == uid for i in info)
    ]

    # get available gpus asc by mem used and reservation counts
    mem_limit = NV_GPU_UNAVAILABLE_ABOVE_MEMORY_USED
    mem_res_gpu = [
        (m, len(gpus_used_by_containers.get(gpu, [])), gpu)
        for gpu, m in gpu_mem_used.items()
    ]
    available_gpus = [
        g for m, r, g in sorted(mem_res_gpu) if mem_limit < 0 or m <= mem_limit
    ]
    if NV_ALLOWED_GPUS != 'ALL':
        available_gpus = [g for g in available_gpus if g in NV_ALLOWED_GPUS]
    logger.debug(
        'available GPUs after mem and allowance filtering: %r', available_gpus)

    if NV_EXCLUSIVE_CONTAINER_GPU_RESERVATION:
        available_gpus = [
            gpu for gpu in available_gpus
            if gpu not in gpus_used_by_containers
        ]

    return available_gpus, gpus_used_by_own_containers
