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

import numpy

from astropy.units import Quantity

from gwpy.timeseries import StateTimeSeries

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

re_limit = re.compile(r'_LIMIT\Z')
re_limen = re.compile(r'_LIMEN\Z')
re_swstat = re.compile(r'_SWSTAT\Z')
re_software = re.compile(
    '(%s)' % '|'.join([re_limit.pattern, re_limen.pattern, re_swstat.pattern]))


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
        return saturation.to_dqflag()
    else:
        return timeseries.times[1:].value[numpy.diff(saturated.astype(int)) > 0]
