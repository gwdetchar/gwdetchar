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

"""gw_data_find wrappers
"""

from __future__ import print_function

import os.path
import warnings

from six import string_types

import gwdatafind

from ..const import DEFAULT_SEGMENT_SERVER

from gwpy.segments import (Segment, DataQualityFlag)
from gwpy.timeseries import TimeSeriesDict

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'


# -- utilities ----------------------------------------------------------------

def check_flag(flag, gpstime, duration, pad):
    """Check that a state flag is active during an entire analysis segment

    Parameters
    ----------
    flag : `str`
        state flag to check

    gpstime : `float`
        GPS time of required data

    duration : `float`
        duration (in seconds) of required data

    pad : `float`
        amount of extra data to read in at the start and end for filtering

    Returns
    -------
    check : `bool`
        Boolean switch to pass (`True`) or fail (`False`) depending on whether
        the given flag is active
    """
    # set GPS start and end time
    start = gpstime - duration/2. - pad
    end = gpstime + duration/2. + pad
    seg = Segment(start, end)
    # query for state segments
    active = DataQualityFlag.query(flag, start, end,
                                   url=DEFAULT_SEGMENT_SERVER).active
    # check that state flag is active during the entire analysis
    if (not active.intersects_segment(seg)) or (abs(active[0]) < abs(seg)):
        return False
    return True


def get_data(channels, gpstime, duration, pad, frametype=None,
             source=None, nproc=1, verbose=False):
    """Retrieve data for a given channel, centered at a given time

    Parameters
    ----------
    channels : `list`
        required data channels

    gpstime : `float`
        GPS time of required data

    duration : `float`
        duration (in seconds) of required data

    pad : `float`
        amount of extra data to read in at the start and end for filtering

    frametype : `str`, optional
        name of frametype in which this channel is stored, by default will
        search for all required frame types

    source : `str`, `list`, optional
        `str` path of a LAL-format cache file or single data file, will
        supercede `frametype` if given, defaults to `None`

    nproc : `int`, optional
        number of parallel processes to use, uses serial process by default

    verbose : `bool`, optional
        print verbose output about NDS progress, default: False

    See Also
    --------
    gwpy.timeseries.TimeSeries.fetch
        for the underlying method to read from an NDS server
    gwpy.timeseries.TimeSeries.read
        for the underlying method to read from a local file cache
    """
    # set GPS start and end time
    start = gpstime - duration/2. - pad
    end = gpstime + duration/2. + pad
    # construct file cache if none is given
    if source is None:
        source = gwdatafind.find_urls(frametype[0], frametype, start, end)
    # read from frames or NDS
    if source:
        return TimeSeriesDict.read(
            source, channels, start=start, end=end, nproc=nproc,
            verbose=verbose)
    return TimeSeriesDict.fetch(channels, start, end, verbose=verbose)
