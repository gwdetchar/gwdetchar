#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of the GW DetChar python (gwdetchar) package.
#
# gwdetchar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwdetchar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Setup the gwdetchar package
"""

from __future__ import print_function

import sys
if sys.version < '2.6':
    raise ImportError("Python versions older than 2.6 are not supported.")

import glob
import os.path

from setuptools import (setup, find_packages)

# set basic metadata
PACKAGENAME = 'gwdetchar'
DISTNAME = 'gwdetchar'
AUTHOR = 'Duncan Macleod'
AUTHOR_EMAIL = 'duncan.macleod@ligo.org'
LICENSE = 'GPLv3'

cmdclass = {}

# -- versioning ---------------------------------------------------------------

import versioneer
__version__ = versioneer.get_version()
cmdclass.update(versioneer.get_cmdclass())

# -- dependencies -------------------------------------------------------------

setup_requires = [
    'pytest-runner',
]
install_requires = [
    'numpy>=1.10',
    'scipy>=0.16',
    'matplotlib>=1.4.1',
    'astropy>=1.2',
    'gwpy>=0.3',
    'trigfind>=0.3',
]
requires = [
    'numpy',
    'matplotlib',
    'astropy',
    'glue',
    'dqsegdb',
    'gwpy',
]
tests_require = [
    'pytest',
]
extras_require = {}

# -- run setup ----------------------------------------------------------------

packagenames = find_packages()
scripts = glob.glob(os.path.join('bin', '*'))

setup(name=DISTNAME,
      provides=[PACKAGENAME],
      version=__version__,
      description=None,
      long_description=None,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url='https://github.com/ligovirgo/gwdetchar',
      packages=packagenames,
      include_package_data=True,
      cmdclass=cmdclass,
      scripts=scripts,
      setup_requires=setup_requires,
      install_requires=install_requires,
      requires=requires,
      extras_require=extras_require,
      dependency_links=[
          'http://software.ligo.org/lscsoft/source/glue-1.49.1.tar.gz'
              '#egg=glue-1.49.1',
          'http://software.ligo.org/lscsoft/source/dqsegdb-1.2.2.tar.gz'
              '#egg=dqsegdb-1.2.2',
          'https://github.com/ligovirgo/trigfind/archive/v0.3.tar.gz'
              '#egg=trigfind-0.3',
      ],
      use_2to3=True,
      classifiers=[
          'Programming Language :: Python',
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Astronomy',
          'Topic :: Scientific/Engineering :: Physics',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          'Operating System :: MacOS',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      ],
      )
