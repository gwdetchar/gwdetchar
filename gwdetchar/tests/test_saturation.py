# -*- coding: utf-8 -*-
# Copyright (C) Joshua Smith (2016-)
#
# This file is part of the GW DetChar python package.
#
# gwdetchar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwdetchar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for :mod:`gwdetchar.saturation`
"""

import pytest

import numpy
from numpy.testing import assert_array_equal

from gwpy.segments import (Segment, SegmentList, DataQualityFlag)
from gwpy.timeseries import (TimeSeries, TimeSeriesDict)
from gwpy.testing.utils import assert_segmentlist_equal
from gwpy.testing.compat import mock

from .. import saturation

# global test objects

DATA = TimeSeries([1, 2, 3, 4, 5, 5, 5, 4, 5, 4], dx=.5, name='X1:TEST_OUTPUT')
SATURATIONS = numpy.array([2., 4.])
SEGMENTS = SegmentList([
    Segment(2., 3.5),
    Segment(4., 4.5),
])

CHANNELS = [
    'X1:TEST_LIMIT',
    'X1:TEST_LIMEN',
    'X1:TEST_SWSTAT',
]
TSDICT = TimeSeriesDict({
    'X1:TEST_LIMEN': TimeSeries(numpy.ones(10), dx=.5, name='X1:TEST_LIMEN'),
    'X1:TEST_OUTPUT': DATA,
    'X1:TEST_LIMIT': TimeSeries(5*numpy.ones(10), dx=.5, name='X1:TEST_LIMIT'),
})


# -- unit tests ---------------------------------------------------------------

def test_find_saturations():
    sats = saturation.find_saturations(DATA, limit=5., segments=False)
    assert_array_equal(sats, SATURATIONS)
    segs = saturation.find_saturations(DATA, limit=5.*DATA.unit, segments=True)
    assert_segmentlist_equal(segs.active, SEGMENTS)


def test_find_saturations_wrapper():
    segs = saturation._find_saturations((DATA, 5.))
    assert_segmentlist_equal(segs.active, SEGMENTS)
    assert segs.name == DATA.name[:-7]


def test_grouper():
    in_ = range(100)
    grouped = list(saturation.grouper(in_, 5))
    expected = [tuple(range(i, i+5)) for i in range(0, 100, 5)]
    assert_array_equal(grouped, expected)


def test_find_limit_channels():
    limens, swstats = saturation.find_limit_channels(CHANNELS)
    assert len(limens) == len(swstats)
    assert_array_equal(limens, ['X1:TEST'])
    assert_array_equal(swstats, ['X1:TEST'])

    limens2, swstats2 = saturation.find_limit_channels(CHANNELS, skip='TEST')
    assert not limens2
    assert not swstats2


@mock.patch('gwdetchar.io.datafind.remove_missing_channels')
@mock.patch('gwpy.timeseries.TimeSeriesDict.read')
def test_is_saturated(tsdfetch, remove):
    tsdfetch.return_value = TSDICT
    remove.return_value = ['X1:TEST_LIMIT']

    saturated = saturation.is_saturated('X1:TEST', 1, start=0, end=8)
    assert isinstance(saturated, DataQualityFlag)
    assert_segmentlist_equal(saturated.active, SEGMENTS)

    saturated2 = saturation.is_saturated(['X1:TEST_LIMIT'], 1, start=0, end=8)
    assert isinstance(saturated2, list)
    assert_segmentlist_equal(saturated2[0].active, saturated.active)

    with pytest.raises(ValueError) as exc:
        saturated3 = saturation.is_saturated(
            'X1:TEST', 1, start=0, end=8, indicator='blah')
    assert str(exc.value).startswith("Don't know how to determine")
