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

import os
import re
from operator import attrgetter

import numpy

from gwdatafind import find_urls

from gwpy.time import to_gps
from gwpy.io.gwf import get_channel_names
from gwpy.timeseries import StateTimeSeries

from . import const
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
                                 accum=True, nds=None):
    """Find the CDS overflow channel names for a given DCUID

    Parameters
    ----------
    dcuid : `int`
        the ID of the front-end controller to search

    ifo : `str`, optional
        the prefix of the interferometer to use

    frametype : `str`, optional
        the frametype to use, defaults to ``{ifo}_R``

    gpstime : `int`, optional
        the GPS time at which to search

    accum : `bool`, optional
        whether to retun the accumulated overflow channels (`True`) or not
        (`False`)

    nds : `str`, optional
        the ``'host:port'`` to use for accessing data via NDS, or `None`
        to use direct GWF file access

    Returns
    -------
    names : `list` of `str`
        the list of channel names found

    """
    ifo = ifo or const.IFO
    if ifo is None:
        raise ValueError("Cannot format channel without an IFO, "
                         "please specify")
    frametype = '{0}_R'.format(ifo)

    if gpstime is None:
        gpstime = int(to_gps('now')) - 1000

    if nds:
        allchannels = _ligo_model_overflow_channels_nds(dcuid, ifo, gpstime,
                                                        nds)
    else:
        allchannels = _ligo_model_overflow_channels_gwf(dcuid, ifo, frametype,
                                                        gpstime)

    if accum:
        regex = re.compile(r'%s:FEC-%d_(ADC|DAC)_OVERFLOW_ACC_\d+_\d+\Z'
                           % (ifo, dcuid))
    else:
        regex = re.compile(r'%s:FEC-%d_(ADC|DAC)_OVERFLOW_\d+_\d+\Z'
                           % (ifo, dcuid))
    return natural_sort(filter(regex.match, allchannels))


def _ligo_model_overflow_channels_nds(dcuid, ifo, gpstime, host):
    import nds2

    if host is True:
        try:
            host = os.getenv('NDSSERVER', '').split(',', 1)[0]
        except KeyError:
            raise ValueError("Cannot determine default NDSSERVER, please pass "
                             "nds=<host:port> or set NDSSERVER environment "
                             "variable")
    try:
        host, port = host.rsplit(':', 1)
    except ValueError:
        connection = nds2.connection(host)
    else:
        connection = nds2.connection(host, int(port))

    if connection.get_protocol() > 1:
        connection.set_epoch(gpstime, gpstime + 1)

    # NOTE: the `3` here is the channel type mask for 'ONLINE | RAW'
    return map(attrgetter('name'), connection.find_channels(
        '{ifo}:FEC-{dcuid}_*_OVERFLOW_*'.format(ifo=ifo, dcuid=dcuid), 3))


def _ligo_model_overflow_channels_gwf(dcuid, ifo, frametype, gpstime):
    try:
        framefile = find_urls(ifo[0], frametype, gpstime, gpstime)[0]
    except IndexError as e:
        e.args = ('No %s-%s frames found at GPS %d'
                  % (ifo[0], frametype, gpstime),)
        raise
    try:
        return _CHANNELS[framefile]
    except KeyError:
        _CHANNELS[framefile] = get_channel_names(framefile)
        return _CHANNELS[framefile]


def find_crossings(timeseries, threshold):
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
        crossing_idx = numpy.nonzero(numpy.diff(
            (timeseries.value >= threshold).astype(int)
        ))[0] + 1
    else:
        crossing_idx = numpy.nonzero(numpy.diff(
            (timeseries.value > threshold).astype(int)
        ))[0] + 1

    return timeseries.times.value[crossing_idx]
