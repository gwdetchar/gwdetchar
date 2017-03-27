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

"""Utilities for analysing ADC or DAC overflows
"""

import re

import numpy

from gwpy.time import tconvert
from gwpy.timeseries import StateTimeSeries

from . import const
from .io.datafind import find_frames
from .utils import natural_sort

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

_CHANNELS = {}


def find_overflows(timeseries, cumulative=True):
    """Find the times of overflows from an overflow counter

    Parameters
    ----------
    timeseries : `~gwpy.timeseries.TimeSeries`
        the input data from the cumulative overflow counter
    cumulative : `bool`, default: `True`
        whether the timeseries contains a cumulative overflow counter
        or an overflow state [0/1]

    Returns
    -------
    times : `numpy.ndarray`
        an array of GPS times (`~numpy.float64`) at which overflows
        were recorded
    """
    if cumulative:
        newoverflow = numpy.diff(
            (numpy.diff(timeseries.value) != 0).astype(int)) > 0
        return timeseries.times.value[2:][newoverflow]
    else:
        newoverflow = numpy.diff(timeseries.value) == 1
        return timeseries.times.value[1:][newoverflow]


def find_overflow_segments(timeseries, cumulative=True, round=False):
    """Find the segments during which the given counter indicated an overflow

    Parameters
    ----------
    timeseries : `~gwpy.timeseries.TimeSeries`
        the input data from the cumulative overflow counter
    cumulative : `bool`, default: `True`
        whether the timeseries contains a cumulative overflow counter
        or an overflow state [0/1]

    Returns
    -------
    overflows : `~gwpy.segments.SegmentList`
        a list of overflow segments
    """
    if cumulative:
        overflowing = (numpy.diff(timeseries) != 0)
        # rejig times after diff
        overflowing.x0 = timeseries.x0 + timeseries.dx
    else:
        overflowing = timeseries.astype(bool)
    return overflowing.view(StateTimeSeries).to_dqflag(
        name=timeseries.name, round=round)


def ligo_accum_overflow_channel(dcuid, ifo=None):
    """Returns the channel name for cumulative overflows for this DCUID

    Parameters
    ----------
    dcuid : `int`
        the DCUID for the relevant front-end model
    ifo : `str`
        the IFO prefix, defaults to the $IFO environment variable

    Returns
    -------
    channel : `str`
        the name of the cumulative overflow counter channel
    """
    ifo = ifo or const.IFO
    if ifo is None:
        raise ValueError("Cannot format channel without an IFO, "
                         "please specify")
    return '%s:FEC-%d_ACCUM_OVERFLOW' % (ifo, dcuid)


def ligo_model_overflow_channels(dcuid, ifo=None, frametype=None, gpstime=None,
                                 accum=True):
    """
    """
    # FIXME: write a docstring
    from lalframe.utils import get_channels

    ifo = ifo or const.IFO
    if ifo is None:
        raise ValueError("Cannot format channel without an IFO, "
                         "please specify")
    if frametype is None:
        frametype = '%s_R' % ifo
    if gpstime is None:
        gpstime = int(tconvert()) - 1000
    try:
        framefile = find_frames(ifo[0], frametype, gpstime, gpstime)[0].path
    except IndexError as e:
        e.args = ('No %s-%s frames found at GPS %d'
                  % (ifo[0], frametype, gpstime),)
        raise
    try:
        allchannels = _CHANNELS[framefile]
    except KeyError:
        _CHANNELS[framefile] = get_channels(framefile)
        allchannels = _CHANNELS[framefile]
    if accum:
        regex = re.compile('%s:FEC-%d_(ADC|DAC)_OVERFLOW_ACC_\d+_\d+\Z'
                           % (ifo, dcuid))
    else:
        regex = re.compile('%s:FEC-%d_(ADC|DAC)_OVERFLOW_\d+_\d+\Z'
                           % (ifo, dcuid))
    return natural_sort(filter(regex.match, allchannels))

def find_crossings(timeseries,threshold):
    """Find the times that a timeseries crosses a specific value

    Parameters
    ----------
    timeseries : `~gwpy.timeseries.TimeSeries`
        the input data to test against a threshold
    threshold : `float`
        function will analyze input timeseries and find times when data 
        crosses this threshold

    Returns
    -------
    times : `numpy.ndarray`
        an array of GPS times (`~numpy.float64`) at which the input data 
        crossed the threshold
    """
    if threshold >= 0:
        crossing_idx = numpy.nonzero(numpy.diff((timeseries.value >= threshold).astype(int)))[0]+1
    else:
        crossing_idx = numpy.nonzero(numpy.diff((timeseries.value > threshold).astype(int)))[0]+1

    return timeseries.times.value[crossing_idx]
