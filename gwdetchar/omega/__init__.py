# coding=utf-8
# Copyright (C) Duncan Macleod (2015)
#
# This file is part of the GW DetChar python package.
#
# GW DetChar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GW DetChar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GW DetChar.  If not, see <http://www.gnu.org/licenses/>.

"""Methods and utilties for performing Omega pipline scans

See Chatterji 2005 [thesis] for details on the Q-pipeline.
"""

import os

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# -- get/set omega paths ------------------------------------------------------

# set default omega install directory
if os.path.isdir('/home/omega/opt/omega'):  # default on LDAS
    os.environ.setdefault('OMEGA_LOCATION', '/home/omega/opt/omega')

# get omega install directory, and path of wpipeline executable
try:
    OMEGA_LOCATION = os.environ['OMEGA_LOCATION']
except KeyError:
    OMEGA_LOCATION = None
    WPIPELINE = None
else:
    WPIPELINE = os.path.join(OMEGA_LOCATION, 'bin', 'wpipeline')

# -- imports ------------------------------------------------------------------

from .scan import *
