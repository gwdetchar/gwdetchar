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

"""Constants for `gwdetchar`
"""

import os

from gwpy.segments import Segment

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

IFO = os.getenv('IFO', None)
ifo = os.getenv('ifo', IFO.lower() if IFO else None)
SITE = os.getenv('SITE', None)
site = os.getenv('site', SITE.lower() if SITE else None)
O1_SEGMENT_SERVER = os.getenv('O1_SEGMENT_SERVER', 'https://segments.ligo.org')
S6_SEGMENT_SERVER = os.getenv('S6_SEGMENT_SERVER',
                              'https://segdb.ligo.caltech.edu')

# -- Run epochs ---------------------------------------------------------------
EPOCH = {
    'ER7': Segment(1117400416, 1118329216),
    'ER8': Segment(1123858817, 1126623617),
    'O1': Segment(1126623617, 1136649617),
    'ER9': Segment(1152136817, 1152255617),
    'ER10': Segment(1161907217, 1164499217),
    'O2': Segment(1164499217, 2000000000),
}
