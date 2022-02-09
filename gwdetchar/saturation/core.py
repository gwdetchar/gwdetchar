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

"""Utilies for analysing sensor saturations
"""

import re
from itertools import zip_longest
from multiprocessing import (cpu_count, Pool)

import numpy
from astropy.units import Quantity

from gwpy.io.cache import file_segment
from gwpy.timeseries import StateTimeSeries

from ..io.datafind import get_data

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Dan Hoak <daniel.hoak@ligo.org>' \
              'Alex Urban <alexander.urban@ligo.org>'

DEFAULT_NPROC = min(8, cpu_count())

re_limit = re.compile(r'_LIMIT\Z')
re_limen = re.compile(r'_LIMEN\Z')
re_swstat = re.compile(r'_SWSTAT\Z')
re_software = re.compile(
    '(%s)' % '|'.join([re_limit.pattern, re_limen.pattern, re_swstat.pattern]))


# -- utilities ----------------------------------------------------------------

def _find_saturations(data):
    """Thin wrapper around find_saturations
    """
    out = find_saturations(
        data[0], data[1], precision=.99, segments=True)
    out.name = out.name[:-7]
    return out


def find_saturations(timeseries, limit=2**16, precision=1, segments=False):
    """Find the times of software saturations of the given `TimeSeries`

    Parameters
    ----------
    timeseries : `~gwpy.timeseries.TimeSeries`
        the input data to search

    limit : `float`, `~gwpy.timeseries.TimeSeries`
        the limit above which a saturation has occurred

    precision : `float` in range (0, 1]
        the precision of the check for saturation

    segments : `bool`, default: `False`
        return saturation segments, otherwise return times when
        saturations occur

    Returns
    -------
    times : `numpy.ndarray`
        the array of times when this timeseries started saturating, OR

    segments : `~gwpy.segments.DataQualityFlag`
        the flag containing segments during which this timeseries
        was actively saturating
    """
    if isinstance(limit, Quantity):
        limit = limit.value
    # check saturated at minimum and maximum
    limit = limit * precision
    saturated = timeseries.value <= -limit
    saturated |= timeseries.value >= limit
    if segments:
        saturation = saturated.view(StateTimeSeries)
        saturation.__metadata_finalize__(timeseries)
        flag = saturation.to_dqflag(
            description="Software saturation indicated by " + timeseries.name,
        )
        flag.isgood = False
        return flag
    else:
        return timeseries.times[1:].value[
            numpy.diff(saturated.astype(int)) > 0]


def grouper(iterable, n, fillvalue=None):
    """Separate an iterable into sub-sets of `n` elements
    """
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def find_limit_channels(channels, skip=None):
    """Find all 'LIMIT' channels that have a matching 'LIMEN' or 'SWSTAT'

    Parameters
    ----------
    channels : `list` of `str`
        the list of channel names to search

    Returns
    -------
    limits : `list` or `str`
        the list of channels whose name ends in '_LIMIT' for whom a matching
        channel ending in '_LIMEN' or '_SWSTAT' was found
    """
    # find relevant channels and sort them
    if skip:
        re_skip = re.compile('(%s)' % '|'.join(skip))
        useful = sorted(x for x in channels if re_software.search(x) and
                        not re_skip.search(x))
    else:
        useful = sorted(x for x in channels if re_software.search(x))

    # map limits to limen or swstat
    limits = sorted(x[:-6] for x in useful if re_limit.search(x))
    limens = sorted(x[:-6] for x in useful if re_limen.search(x)
                    and x[:-6] in limits)
    swstats = sorted(x[:-7] for x in useful if re_swstat.search(x)
                     and x[:-7] in limits)
    return (limens, swstats)


def is_saturated(channel, cache, start=None, end=None, indicator='LIMEN',
                 nproc=DEFAULT_NPROC):
    """Check whether a channel has saturated its software limit

    Parameters
    ----------
    channel : `str`, or `list` of `str`
        either a single channel name, or a list of channel names

    cache : `list`
        a `list` of file paths, the cache must be contiguous

    start : `~gwpy.time.LIGOTimeGPS`, `int`
        the GPS start time of the check

    end : `~gwpy.time.LIGOTimeGPS`, `int`
        the GPS end time of the check

    indicator : `str`
        the suffix of the indicator channel, either `'LIMEN'` or `'SWSTAT'`

    nproc : `int`
        the number of parallel processes to use for frame reading

    Returns
    -------
    saturated : `bool`, `None`, or `DataQualityFlag`, or `list` of the same
        one of the following given the conditions
        - `None` : if the channel doesn't have a software limit
        - `False` : if the channel didn't saturate
        - `~gwpy.segments.DataQualityFlag` : otherwise
        OR, a `list` of the above if a `list` of channels was given in the
        first place
    """
    if isinstance(channel, (list, tuple)):
        channels = channel
    else:
        channels = [channel]
    # parse prefix
    for i, c in enumerate(channels):
        if c.endswith('_LIMIT'):
            channels[i] = c[:-6]
    # check limit if set
    indicators = ['{}_{}'.format(c, indicator) for c in channels]
    gps = file_segment(cache[0])[0]
    data = get_data(indicators, gps, gps+1, source=cache, nproc=nproc)

    # check limits for returned channels
    if len(data) < len(channels):  # exclude nonexistent channels
        channels = [
            c for c in channels if '{}_{}'.format(c, indicator) in data]
        indicators = ['{}_{}'.format(c, indicator) for c in channels]
    if indicator.upper() == 'LIMEN':
        active = dict((c, data[indicators[i]].value[0]) for
                      i, c in enumerate(channels))
    elif indicator.upper() == 'SWSTAT':
        active = dict(
            (c, data[indicators[i]].astype('uint32').value[0] >> 13 & 1) for
            i, c in enumerate(channels))
    else:
        raise ValueError("Don't know how to determine if limit is set for "
                         "indicator %r" % indicator)
    # get output/limit data for all with active limits
    activechans = [c for c in channels if active[c]]
    datachans = ['%s_%s' % (c, s) for c in activechans for
                 s in ('LIMIT', 'OUTPUT')]
    data = get_data(datachans, start, end, source=cache, nproc=nproc)

    # find saturations of the limit for each channel
    dataiter = ((data['%s_OUTPUT' % c], data['%s_LIMIT' % c])
                for c in activechans)
    if nproc > 1:
        with Pool(processes=nproc) as pool:
            saturations = list(pool.map(_find_saturations, dataiter))
    else:
        saturations = list(map(_find_saturations, dataiter))

    # return many or one (based on input)
    if isinstance(channel, (list, tuple)):
        return saturations
    else:
        return saturations[0]
