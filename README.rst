Userdocker
==========

Userdocker is a wrapper that allows admins to grant restricted docker
commandline access to users.

.. note::

    Userdocker is currently in BETA state. Despite our ongoing efforts to test
    on our local infrastructure, further testing, reviewing and feedback are
    very welcome. Use with caution and watch the GitHub repo for issues and
    new releases!


Userdocker is aimed towards scientific high performance computing and cluster
setups, as they exist in most universities or research groups. Often, such
scientific computations have peculiar dependencies that are difficult to satisfy
across linux distributions (and drive admins crazy ;) ).

In theory such use-cases could largely benefit from docker, as it would allow
users to easily define environments themselves and run them basically without
negative performance impact, as they run directly on the host's kernel. In
reality however granting docker commandline access to users effectively makes
them root equivalent on the host (root in container, volume mount...), making
this prohibitive for cluster computing.

Userdocker solves this problem by wrapping the docker command and just making
the safe parts available to users. Admins can decide what they consider safe
(with sane defaults). The userdocker command largely follows the docker
commandline syntax, so users can use it as an in-place replacement for the
docker command.

Feedback / bugreports / contributions welcome:

https://github.com/joernhees/userdocker


Sample Usage:
=============

.. code-block:: bash

    # command line help (including subcommands the user is allowed to execute)
    sudo userdocker -h

    # (docker images) list images (and useful tree visualization)
    sudo userdocker images
    sudo userdocker dockviz

    # (docker run) run a debian image with user (read-only) mounted home
    sudo userdocker run -it --rm -v $HOME:$HOME:ro debian bash

    # (docker ps) list running containers
    sudo userdocker ps

    # (docker pull / load) pull or load
    sudo userdocker pull debian
    sudo userdocker load < image.tar.gz

    # (nvidia-docker) extensions for nvidia GPU support
    alias nvidia-userdocker='userdocker --executor=nvidia-docker'
    NV_GPU=1,3,7 nvidia-userdocker run -it --rm nvcr.io/nvidia/tensorflow
    userdocker ps --gpu-used
    userdocker ps --gpu-free

Features:
=========

- Similar commandline interface as ``docker ...`` called ``userdocker ...``
- Support for several docker commands / plugins (docker, nvidia-docker)
- Fine granular configurability for admins in ``/etc/userdocker/`` allows to:

   - restrict runnable images if desired (allows admin reviews)
   - restrict run to locally available images
   - restrict available mount points (or enforce them, or default mount)
   - probe mounts (to make sure nfs automounts don't make docker sad)
   - enforce non-root user in container (same uid:gid as on host)
   - enforce dropping caps
   - enforce environment vars
   - enforce docker args
   - restrict port publishing
   - explicitly white-list available args to user
   - restrict allowed GPU access / reservations via ``NV_GPU``

- System wide config + overrides for individual groups, gids, users, uids.
- Easy extensibility for further subcommands and args.


Installation:
=============

The installation of userdocker works in three steps:


1. Install package:
-------------------

First make sure that docker is installed:

.. code-block:: bash

    sudo docker version

Afterwards, as userdocker is written in python3 and available as python package:

.. code-block:: bash

    sudo pip3 install userdocker

This will give you a ``userdocker`` command that you can test with:

.. code-block:: bash

    userdocker -h

The above is the preferable way of installation.

Alternatively, you can clone this repo and execute:

.. code-block:: bash

    sudo python3 setup.py install


2. Configuration:
-----------------

Copy the default config to ``/etc/userdocker/config.py``, then edit the file.
The config contains tons of comments and explanations to help you make the right
decisions for your scenario.

.. code-block:: bash

    sudo cp /etc/userdocker/default.py /etc/userdocker/config.py


3. Allowing users to run ``sudo userdocker``:
---------------------------------------------

You should now allow the users in question to run ``sudo userdocker``. This is
basically done by adding a ``/etc/sudoers.d/userdocker`` file. If you want to
grant this permission to all users in group ``users``, add the following
two lines:

::

    Defaults env_keep += "NV_GPU"
    %users ALL=(root) NOPASSWD: /usr/local/bin/userdocker

The first is strongly recommended in case you want to allow users to use nvidia
GPUs from within docker containers via nvidia-docker (see EXECUTORS in config).
Without it they cannot pass the NV_GPU environment variable to the userdocker
(and thereby nvidia-docker) command to select their desired GPU(s).


FAQ:
====

Why sudo?
---------

Because it supports logging and is in general a lot more configurable than the
alternatives. For example if you only want to make ``userdocker`` available on
some nodes in your cluster, you can use the Host\_List field:

::

    %users node1,node2,node4=(root) /usr/local/bin/userdocker

