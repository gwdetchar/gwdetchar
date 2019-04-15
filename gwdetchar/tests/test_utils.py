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

"""Tests for :mod:`gwdetchar.utils`
"""

import pytest

import numpy

from gwpy.segments import (
    DataQualityFlag,
    DataQualityDict,
)
from gwpy.table import EventTable
from gwpy.testing.utils import assert_table_equal

from .. import utils


@pytest.mark.parametrize('in_, out', [
    ([1, 2, 3], [1, 2, 3]),
    ([1, 10, 2, 3], [1, 2, 3, 10]),
    (['1', '10', '2', '3'], ['1', '2', '3', '10']),
    (['a', 'b', 'd', 'c'], ['a', 'b', 'c', 'd']),
])
def test_natural_sort(in_, out):
    assert utils.natural_sort(in_) == out


def test_table_from_segments():
    segs = DataQualityDict()
    segs["test1"] = DataQualityFlag(
        active=[(0, 1), (3, 4)],
    )
    segs["test2"] = DataQualityFlag(
        active=[(5, 6)],
    )
    assert_table_equal(
        utils.table_from_segments(segs),
        EventTable(
            rows=[(0., 100., 0., 1., 10., "test1"),
                  (3., 100., 3., 4., 10., "test1"),
                  (5., 100., 5., 6., 10., "test2")],
            names=("time", "frequency", "start_time", "end_time",
                   "snr", "channel"),
        ),
    )
    assert_table_equal(
        utils.table_from_segments(
            segs,
            frequency=1234.,
            snr=-4.,
            sngl_burst=True),
        EventTable(
            rows=[(0., 1234., -4., "test1"),
                  (3., 1234., -4., "test1"),
                  (5., 1234., -4., "test2")],
            names=("peak", "peak_frequency", "snr", "channel"),
        ),
    )


def test_table_from_segments_empty():
    segs = DataQualityDict()
    segs['test'] = DataQualityFlag(
       active=[]
    )
    assert_table_equal(
        utils.table_from_segments(segs),
        EventTable(
            names=("time", "frequency", "start_time", "end_time",
                   "snr", "channel")
        )
    )


def test_table_from_times():
    times = numpy.array(range(10), dtype=float)
    assert_table_equal(
        utils.table_from_times(times),
        EventTable([times, [100.] * 10, [10.] * 10],
                   names=("time", "frequency", "snr")),
    )
