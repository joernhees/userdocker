# -*- coding: utf-8 -*-
import json
import re
from collections import defaultdict
from operator import itemgetter

from ..config import NVIDIA_SMI
from ..config import NV_ALLOWED_GPUS
from ..config import NV_EXCLUSIVE_CONTAINER_GPU_RESERVATION
from ..config import NV_GPU_UNAVAILABLE_ABOVE_MEMORY_USED
from .execute import exec_cmd


def nvidia_get_gpus_used_by_containers(docker):
    running_containers = exec_cmd(
        [docker, 'ps', '-q'],
        return_status=False,
    ).split()
    if not running_containers:
        return {}
    gpu_used_by_containers_str = exec_cmd(
        [
            docker, 'inspect', '--format',
            '[{{json .Name}}, {{json .Id}}, {{json .Config.Env}}, '
            '{{json $.HostConfig.Devices}}]'
        ] + running_containers,
        return_status=False,
    )
    gpu_dev_id_re = re.compile('^/dev/nvidia([0-9]+)$')
    gpu_used_by_containers = defaultdict(list)
    for line in gpu_used_by_containers_str.splitlines():
        container_name, container, env, devs = json.loads(line)
        for dev in devs:
            d = dev.get('PathOnHost', '')
            m = gpu_dev_id_re.match(d)
            if m:
                gpu_id = m.groups()
                userdocker_user = [
                    e.split('=', 1)[1]
                    for e in env if e.startswith('USERDOCKER_USER=')
                ]
                user = userdocker_user[0] if userdocker_user else ''
                gpu_used_by_containers[gpu_id].append(
                    (container, container_name, user)
                )
    return gpu_used_by_containers


def nvidia_get_available_gpus(docker, nvidia_smi=NVIDIA_SMI):
    if not NV_ALLOWED_GPUS:
        return []

    gpu_mem_used_str = exec_cmd(
        [nvidia_smi,
         '--query-gpu=index,memory.used,utilization.gpu',
         '--format=csv'],
        return_status=False,
    )
    gpu_mem_used = {}
    for line in gpu_mem_used_str.splitlines()[1:]:  # skip header
        gpu, mem_used, gpu_utilization = line.split(', ')
        gpu = int(gpu)
        mem_used = int(mem_used.split(' MiB')[0])
        gpu_mem_used[gpu] = mem_used

    # get available gpus asc by mem used
    available_gpus = [
        g for g, m in sorted(gpu_mem_used.items(), key=itemgetter(1, 0))
        if m <= NV_GPU_UNAVAILABLE_ABOVE_MEMORY_USED
    ]
    if NV_ALLOWED_GPUS != 'ALL':
        available_gpus = [g for g in available_gpus if g in NV_ALLOWED_GPUS]

    if not NV_EXCLUSIVE_CONTAINER_GPU_RESERVATION:
        return available_gpus

    gpus_used_by_containers = nvidia_get_gpus_used_by_containers(docker)
    return [gpu for gpu in available_gpus if gpu not in gpus_used_by_containers]
