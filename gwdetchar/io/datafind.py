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

import warnings

import gwdatafind

from ..const import DEFAULT_SEGMENT_SERVER

from gwpy.io import gwf as io_gwf
from gwpy.segments import (Segment, DataQualityFlag)
from gwpy.timeseries import (TimeSeries, TimeSeriesDict)

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


def remove_missing_channels(channels, gwfcache):
    """Find and remove channels from a given list that are not available in
    a given cache of frame files

    Parameters
    ----------
    channels : `list` of `str`
        list of requested channels

    gwfcache : `list` of `str`
        list of paths to .gwf files

    Returns
    -------
    keep : `list` of `str`
        list of common channels found in the first and last files in the
        cache

    Notes
    -----
    As a shorthand, this utility checks `channels` against only the first
    and last frame files in `gwfcache`. This saves time and memory by not
    loading tables of contents for large numbers of very long data files.

    For every channel requested that is not available in `gwfcache`, a
    `UserWarning` will be raised.

    See Also
    --------
    gwpy.io.gwf.iter_channel_names
        for the utility used to identify frame contents
    """
    # get available channels from the first and last frame file
    available = set(io_gwf.iter_channel_names(gwfcache[0]))
    if len(gwfcache) > 1:
        available.intersection_update(io_gwf.iter_channel_names(gwfcache[-1]))
    # work out which channels to keep, and which to reject
    channels = set(channels)
    keep = channels & available
    reject = channels - keep
    for channel in reject:
        warnings.warn(
            '{} is being removed because it was not available in all '
            'requested files'.format(channel), UserWarning)
    return list(keep)


def get_data(channel, start, end, obs=None, frametype=None, source=None,
             nproc=1, verbose=False, **kwargs):
    """Retrieve data for given channels within a certain time range

    Parameters
    ----------
    channel : `str` or `list`
        either a single channel name, or a list of channel names

    start : `float`
        GPS start time of requested data

    end : `float`
        GPS end time of requested data

    obs : `str`, optional
        single-letter name of observatory, defaults to the first letter of
        `frametype`

    frametype : `str`, optional
        name of frametype in which channel(s) are stored, required if `source`
        is `None`

    source : `str`, `list`, optional
        `str` path(s) of a LAL-format cache file or individual data file, will
        supercede `frametype` if given, defaults to `None`

    nproc : `int`, optional
        number of parallel processes to use, uses serial process by default

    verbose : `bool`, optional
        print verbose output about NDS progress, default: False

    **kwargs : `dict`, optional
        additional keyword arguments to `~gwpy.timeseries.TimeSeries.read`
        or `~gwpy.timeseries.TimeSeries.fetch`

    Returns
    -------
    data : `~gwpy.timeseries.TimeSeries` or `~gwpy.timeseries.TimeSeriesDict`
        collection of data for the requested channels in the requested time
        range

    Notes
    -----
    If `channel` is a `str`, then a `TimeSeries` object will be returned, else
    the result is a `TimeSeriesDict`.

    See Also
    --------
    gwpy.timeseries.TimeSeries.fetch
        for the underlying method to read from an NDS server
    gwpy.timeseries.TimeSeries.read
        for the underlying method to read from a local file cache
    """
    # get TimeSeries class
    if isinstance(channel, (list, tuple)):
        series_class = TimeSeriesDict
    else:
        series_class = TimeSeries
    # construct file cache if none is given
    if source is None:
        obs = obs if obs is not None else frametype[0]
        source = gwdatafind.find_urls(obs, frametype, start, end)
    # read from frames or NDS
    if source:
        if isinstance(channel, (list, tuple)):
            channel = remove_missing_channels(channel, source)
        return series_class.read(
            source, channel, start=start, end=end, nproc=nproc,
            verbose=verbose, **kwargs)
    elif isinstance(channel, str):
        return series_class.fetch(
            channel, start, end, verbose=verbose, **kwargs)
    # if all else fails, process channels in groups of 60
    data = series_class()
    for group in [channel[i:i + 60] for i in range(0, len(channel), 60)]:
        data.append(series_class.fetch(
            group, start, end, verbose=verbose, **kwargs))
    return data
