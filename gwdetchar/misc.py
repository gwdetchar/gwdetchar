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

"""Miscellaneous methods and utilities
"""

import numpy

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def find_timeseries_value_changes(timeseries):
    """Find the times of changes in the value of a `TimeSeries`

    Parameters
    ----------
    timeseries : `~gwpy.timeseries.TimeSeries`
        the input data series

    Returns
    -------
    times : `numpy.ndarray`
        an array of GPS times (`~numpy.float64`) at which the given
        timeseries changed value
    """
    diff = numpy.diff(timeseries.value)
    times = timeseries.times.value[1:]
    return times[diff > 0]
