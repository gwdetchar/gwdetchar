# coding=utf-8
# Copyright (C) Alex Urban (2019)
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

"""Methods and utilties for optical scattering
"""

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>' \
              'Joshua Smith <joshua.smith@ligo.org>' \
              'Andrew Lundgren <andrew.lundgren>@ligo.org>'

# import scattering utils
from .core import (
    OPTIC_MOTION_CHANNELS,
    TRANSMON_CHANNELS,
    FREQUENCY_MULTIPLIERS,
    get_fringe_frequency,
    get_blrms,
    get_segments,
)

# global figure captions
SCATTER_CAPTION = 'Evidence for scattering in {CHANNEL}. Top: longitudinal ' \
                  'optic motion; second row: projected fringe frequency of ' \
                  'the first four harmonics; third row: time-frequency ' \
                  'scatter plot of Omicron triggers, coloured by signal-to-' \
                  'noise ratio; bottom: known (small) and active (large) ' \
                  'time segments when one harmonic is above the frequency ' \
                  'threshold.'
HIST_CAPTION = 'Cumulative histogram of the total time with fringe ' \
               'frequency above a given value. The first (red), second ' \
               '(green), third (gold), and fourth (blue) harmonics are ' \
               'shown for {CHANNEL}.'
