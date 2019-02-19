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

try:  # python 3.x
    from urllib.parse import urlparse
except ImportError:  # python 2.x
    from urlparse import urlparse

import gwdatafind

from ..const import DEFAULT_SEGMENT_SERVER

from gwpy.segments import (Segment, DataQualityFlag)
from gwpy.timeseries import TimeSeriesDict

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'


def find_frames(site, frametype, gpsstart, gpsend, urltype='file', **kwargs):
    """Find frames for given site and frametype
    """
    warnings.warn("this function is deprecated, use `gwdatafind.find_urls` "
                  "directly", DeprecationWarning)
    return gwdatafind.find_urls(site[0], frametype, gpsstart, gpsend,
                                urltype=urltype, **kwargs)


def write_omega_cache(cache, fobj):
    """Write a :class:`~glue.lal.Cache` of files to file in Omega format

    The Omega pipeline expects a file cache in a specific, custom format:

    {observatory} {frametype} {gpsstart} {gpsend} {fileduration} {directory}
    """
    # open filepath
    if isinstance(fobj, string_types):
        with open(fobj, 'w') as f:
            return write_omega_cache(cache, f)

    # convert to omega cache format
    wcache = {}
    for e in cache:
        dir_ = os.path.split(e.path)[0]
        if dir_ in wcache:
            l = wcache[dir_]
            if l[2] > int(e.segment[0]):
                wcache[dir_][2] = e.segment[0]
            if l[3] < int(e.segment[1]):
                wcache[dir_][3] = e.segment[1]
        else:
            wcache[dir_] = [e.observatory, e.description,
                            int(e.segment[0]), int(e.segment[1]),
                            int(abs(e.segment)), dir_]

    # write to file
    for item in wcache:
        print(' '.join(map(str, wcache[item])), file=fobj)


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


def get_data(channels, gpstime, duration, pad, frametype=None, source=None,
             dtype='float64', nproc=1, verbose=False):
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
    dtype : `str` or `dtype`, optional
        typecode or data-type to which the output `TimeSeries` is cast
    nproc : `int`, optional
        number of parallel processes to use, uses serial process by default
    verbose : `bool`, optional
        print verbose output about NDS progress, default: False

    See Also
    --------
    gwpy.timeseries.TimeSeries.get
        for the underlying method to read from frames or NDS
    gwpy.timeseries.TimeSeries.read
        for the underlying method to read from a local file cache
    """
    # set GPS start and end time
    start = gpstime - duration/2. - pad
    end = gpstime + duration/2. + pad
    # construct file cache if none is given
    if source is None:
        cache = gwdatafind.find_urls(frametype[0], frametype, start, end)
        source = [urlparse(fileobj).path for fileobj in cache]
    # read from frames or NDS
    if source:
        return TimeSeriesDict.read(
            source, channels, start=start, end=end, nproc=nproc,
            verbose=verbose, dtype=dtype)
    return TimeSeriesDict.fetch(channels, start, end, verbose=verbose,
                                dtype=dtype)
