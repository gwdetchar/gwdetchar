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

"""Data discovery utilities
"""

import re
import numpy
import warnings
from urllib.error import HTTPError
from json.decoder import JSONDecodeError

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


def get_data(channel, start, end, frametype=None, source=None,
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

    frametype : `str`, optional
        name of frametype in which channel(s) are stored, default: `None`

    source : `str`, `list`, optional
        path(s) of a LAL-format cache file or individual data file,
        default: `None`

    nproc : `int`, optional
        number of parallel processes to use, uses serial process by default

    verbose : `bool`, optional
        print verbose output about NDS progress, default: False

    **kwargs : `dict`, optional
        additional keyword arguments to `~gwpy.timeseries.TimeSeries.read`
        or `~gwpy.timeseries.TimeSeries.get`

    Returns
    -------
    data : `~gwpy.timeseries.TimeSeries` or `~gwpy.timeseries.TimeSeriesDict`
        collection of data for the requested channels in the requested time
        range

    Notes
    -----
    If `channel` is a `str`, then a `TimeSeries` object will be returned, else
    the result is a `TimeSeriesDict`.

    The `frametype` argument should be used to read from archived frame files,
    while `source` should be used to read from a local cache or specific data
    file. If either fails, or if neither is passed, this function will attempt
    to get data over an NDS server.

    If `frametype` is used to read from the archive, any channels missing
    from the first or last frame file in the requested time range will be
    ignored.

    See Also
    --------
    remove_missing_channels
        a utility that removes channels missing from the frame archive
    gwpy.timeseries.TimeSeries.get
        the underlying method to read data over an NDS server
    gwpy.timeseries.TimeSeries.read
        the underlying method to read data from local files
    """
    # get TimeSeries class
    if isinstance(channel, (list, tuple)):
        series_class = TimeSeriesDict
    else:
        series_class = TimeSeries

    if frametype is not None:
        try:  # locate frame files
            ifo = re.search('[A-Z]1', frametype).group(0)
            obs = ifo[0]
            source = gwdatafind.find_urls(obs, frametype, start, end)
        except AttributeError:
            raise AttributeError(
                'Could not determine observatory from frametype')
        except (HTTPError, JSONDecodeError):  # frame files not found
            pass
    if isinstance(source, list) and isinstance(channel, (list, tuple)):
        channel = remove_missing_channels(channel, source)
    if source is not None:  # read from frame files
        return series_class.read(
            source, channel, start=start, end=end, nproc=nproc,
            verbose=verbose, **kwargs)

    # read single channel from NDS
    if not isinstance(channel, (list, tuple)):
        return series_class.get(
            channel, start, end, verbose=verbose, **kwargs)

    # if all else fails, process channels in groups of 60
    data = series_class()
    for group in [channel[i:i + 60] for i in range(0, len(channel), 60)]:
        data.append(series_class.get(
            group, start, end, verbose=verbose, **kwargs))
    return data


def downselect(frametype, start, end, preview=10, channels=[],
               search=[], dynamic=True, **kwargs):
    """Pare down the full set of channels in a frametype based on
    properties of the data

    Parameters
    ----------
    frametype : `str`
        name of archived frametype to analyze

    start : `float`
        GPS start time of requested data

    end : `float`
        GPS end time of requested data

    preview : `float`, default
        length of time (seconds) to determine data properties at the
        beginning, default: 10 seconds

    channels : `list` of `str`, optional
        list of channel names to select, default: none

    search : `list` of `str`, optional
        list of regular expression patterns to search for, default: none

    dynamic : `bool`, optional
        Boolean switch to include (`True`) or exclude (`False`) dynamic
        data channels, defaults to including them

    **kwargs : `dict`, optional
        additional keyword arguments to `get_data`

    Returns
    -------
    out : `tuple` of `list`
        a collection of lists corresponding to channel name, initial value,
        final value, and net difference
    """
    # get paths to frame files
    obs = re.search('[A-Z]1', frametype).group(0)[0]
    cache1 = gwdatafind.find_urls(obs, frametype, start-preview, start)
    cache2 = gwdatafind.find_urls(obs, frametype, end, end+preview)
    # get list of channels to analyze
    available = (set(io_gwf.iter_channel_names(cache1[-1])) &
        set(io_gwf.iter_channel_names(cache2[0])))
    channels = list(set(channels) & available) or list(available)
    if search:  # select channels matching regex patterns
        requested = re.compile('({})'.format('|'.join(search)))
        channels = [c for c in channels if requested.search(c)]
    # get preview data from frames
    data1 = get_data(channels, start-preview, start, source=cache1,
                     verbose='Reading initial preview:'.rjust(30), **kwargs)
    data2 = get_data(channels, end, end+preview, source=cache2,
                     verbose='Reading final preview:'.rjust(30), **kwargs)
    # identify channels
    changes = [c for c in channels
               if (dynamic and not all(numpy.diff(data1[c].value)))
               or (data1[c].value[-1] != data2[c].value[0])]
    # record state changes and return
    initial = [data1[c].value[-1] for c in changes]
    final = [data2[c].value[0] for c in changes]
    diff = [y - x for x, y in zip(initial, final)]
    return (changes, initial, final, diff, channels)
