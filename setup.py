# -*- coding: utf-8 -*-
from os import path
from setuptools import find_packages
from setuptools import setup

from userdocker import __doc__
from userdocker import __version__

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='userdocker',
    version=__version__,
    description=__doc__.strip().splitlines()[0].strip(),
    long_description=long_description,
    url='https://github.com/joernhees/userdocker',
    author='Jörn Hees',
    author_email='dev+userdocker@joernhees.de',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
        'Topic :: Security',
        'Topic :: Software Development',
        'Topic :: System',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Emulators',
        'Topic :: System :: Operating System',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: Utilities',
    ],
    keywords='docker user limit admin hpc cluster computing permissions',
    packages=find_packages(),
    data_files=[('/etc/userdocker/', ['userdocker/config/default.py'])],
    entry_points={'console_scripts': ['userdocker=userdocker.userdocker:main']},
    zip_safe=True,
)
