# -*- coding: utf-8 -*-
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
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for `gwdetchar.io.datafind`
"""

import pytest

import numpy
from numpy import testing as nptest

from unittest import mock

from gwpy.timeseries import (TimeSeries, TimeSeriesDict)
from gwpy.segments import (Segment, DataQualityFlag)

from .. import datafind

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

HOFT = TimeSeries(
    numpy.random.normal(loc=1, scale=.5, size=16384 * 66),
    sample_rate=16384, epoch=0, name='X1:TEST-STRAIN')

FLAG = DataQualityFlag(known=[(-33, 33)], active=[(-33, 33)],
                       name='X1:TEST-FLAG:1')


# -- make sure data can be read -----------------------------------------------

@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG)
def test_check_flag(segserver):
    # attempt to query segments database for an analysis flag
    flag = 'X1:TEST-FLAG:1'
    assert datafind.check_flag(flag, gpstime=0, duration=64, pad=1) is True
    assert datafind.check_flag(flag, gpstime=800, duration=64, pad=1) is False


@mock.patch('gwpy.io.gwf.iter_channel_names', return_value=['X1:TEST-STRAIN'])
def test_remove_missing_channels(io_gwf):
    channels = datafind.remove_missing_channels(
        ['X1:TEST-STRAIN'], 'test.cache')
    assert channels == ['X1:TEST-STRAIN']

    with pytest.warns(UserWarning, match='is being removed because'):
        channels = datafind.remove_missing_channels(
            ['X1:TEST-STRAIN', 'X1:TEST-STRAIN_NONEXISTENT'], 'test.cache')
        assert channels == ['X1:TEST-STRAIN']


@mock.patch('gwpy.timeseries.TimeSeries.get', return_value=HOFT)
def test_get_data_from_NDS(tsget):
    # retrieve data
    start = 0
    end = 64
    channel = 'X1:TEST-STRAIN'
    data = datafind.get_data(channel, start, end)

    # test data products
    assert isinstance(data, TimeSeries)
    nptest.assert_array_equal(data.value, HOFT.value)


@mock.patch('gwpy.timeseries.TimeSeriesDict.get',
            return_value=TimeSeriesDict({'X1:TEST-STRAIN': HOFT}))
def test_get_data_dict_from_NDS(tsdget):
    # retrieve data
    start = 33
    end = 64
    channels = ['X1:TEST-STRAIN']
    data = datafind.get_data(channels, start, end)

    # test data products
    assert isinstance(data, TimeSeriesDict)
    nptest.assert_array_equal(data['X1:TEST-STRAIN'].value, HOFT.value)


@mock.patch('gwpy.io.datafind.find_urls')
@mock.patch('gwpy.timeseries.TimeSeries.read')
def test_get_data_from_cache(tsget, find_data):
    # set return values
    find_data.return_value = ['test.gwf']
    tsget.return_value = HOFT.crop(16, 48)

    # retrieve test frame
    start = 16
    end = start + 32
    channel = 'X1:TEST-STRAIN'
    frametype = 'X1_TEST'
    data = datafind.get_data(channel, start, end, frametype=frametype)

    # test data products
    assert isinstance(data, TimeSeries)
    assert data.duration.value == 32
    assert data.span == Segment(start, end)
    nptest.assert_array_equal(data.value, HOFT.crop(start, end).value)


@mock.patch('gwpy.io.datafind.find_urls')
@mock.patch('gwdetchar.io.datafind.remove_missing_channels')
@mock.patch('gwpy.timeseries.TimeSeriesDict.read')
def test_get_data_dict_from_cache(tsdget, remove, find_data):
    # set return values
    tsdget.return_value = TimeSeriesDict({
        'X1:TEST-STRAIN': HOFT.crop(16, 48)})
    remove.return_value = ['X1:TEST-STRAIN']
    find_data.return_value = ['test.gwf']
    # retrieve test frame
    start = 16
    end = start + 32
    channels = ['X1:TEST-STRAIN']
    data = datafind.get_data(channels, start, end, source=True)

    # test data products
    assert isinstance(data, TimeSeriesDict)
    assert data[channels[0]].duration.value == 32
    assert data[channels[0]].span == Segment(start, end)
    nptest.assert_array_equal(data[channels[0]].value,
                              HOFT.crop(start, end).value)


def test_get_data_bad_frametype():
    channel = 'X1:TEST-STRAIN'
    with pytest.raises(AttributeError) as exc:
        datafind.get_data(channel, start=0, end=32, frametype='bad_frametype')
    assert 'Could not determine observatory' in str(exc.value)
