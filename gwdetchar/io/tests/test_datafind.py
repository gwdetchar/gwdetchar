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

import os
import shutil

import pytest

import numpy
from numpy import testing as nptest

from gwpy.testing import utils
from gwpy.testing.compat import mock
from gwpy.timeseries import (TimeSeries, TimeSeriesDict)
from gwpy.segments import (Segment, DataQualityFlag)

from .. import datafind

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

HOFT = TimeSeries(
    numpy.random.normal(loc=1, scale=.5, size=16384 * 66),
    sample_rate=16384, epoch=0, name='X1:TEST-STRAIN')

FLAG = DataQualityFlag(known=[(0, 66)], active=[(0, 66)],
                       name='X1:TEST-FLAG:1')


# -- make sure data can be read -----------------------------------------------

@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG)
def test_check_flag(segserver):
    # attempt to query segments database for an analysis flag
    gpstime = 0
    duration = 64
    pad = 1
    flag = 'X1:TEST-FLAG:1'
    assert datafind.check_flag(flag, gpstime, duration, pad) is True


@mock.patch('gwpy.timeseries.TimeSeries.fetch', return_value=HOFT)
def test_get_data_from_NDS(tsfetch):
    # retrieve data
    start = 0
    end = 64
    channel = 'X1:TEST-STRAIN'
    data = datafind.get_data(channel, start, end, source=0)

    # test data products
    assert isinstance(data, TimeSeries)
    nptest.assert_array_equal(data.value, HOFT.value)


@mock.patch('gwpy.timeseries.TimeSeriesDict.fetch',
            return_value=TimeSeriesDict({'X1:TEST-STRAIN': HOFT}))
def test_get_data_dict_from_NDS(tsdfetch):
    # retrieve data
    start = 33
    end = 64
    channels = ['X1:TEST-STRAIN']
    data = datafind.get_data(channels, start, end, source=0)

    # test data products
    assert isinstance(data, TimeSeriesDict)
    nptest.assert_array_equal(data['X1:TEST-STRAIN'].value, HOFT.value)


def test_get_data_from_cache(tmpdir):
    # set up a data file
    os.chdir(str(tmpdir))
    HOFT.write('test.gwf')

    # retrieve test frame
    start = 16
    end = start + 32
    channel = 'X1:TEST-STRAIN'
    data = datafind.get_data(channel, start, end, source='test.gwf')

    # test data products
    assert isinstance(data, TimeSeries)
    assert data.duration.value == 32
    assert data.span == Segment(start, end)
    nptest.assert_array_equal(data.value, HOFT.crop(start, end).value)
    shutil.rmtree(str(tmpdir), ignore_errors=True)


def test_get_data_dict_from_cache(tmpdir):
    # set up a data file
    os.chdir(str(tmpdir))
    HOFT.write('test.gwf')

    # retrieve test frame
    start = 16
    end = start + 32
    channels = ['X1:TEST-STRAIN']
    data = datafind.get_data(channels, start, end, source='test.gwf')

    # test data products
    assert isinstance(data, TimeSeriesDict)
    assert data[channels[0]].duration.value == 32
    assert data[channels[0]].span == Segment(start, end)
    nptest.assert_array_equal(data[channels[0]].value,
                              HOFT.crop(start, end).value)
    shutil.rmtree(str(tmpdir), ignore_errors=True)
