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

import numpy
from numpy.testing import assert_array_equal

from gwpy.segments import (Segment, SegmentList)
from gwpy.timeseries import TimeSeries
from gwpy.testing.utils import assert_segmentlist_equal

from .. import saturation

DATA = TimeSeries([1, 2, 3, 4, 5, 5, 5, 4, 5, 4], dx=.5)
SATURATIONS = numpy.array([2., 4.])
SEGMENTS = SegmentList([
    Segment(2., 3.5),
    Segment(4., 4.5),
])


def test_find_saturations():
    sats = saturation.find_saturations(DATA, limit=5., segments=False)
    assert_array_equal(sats, SATURATIONS)
    segs = saturation.find_saturations(DATA, limit=5.*DATA.unit, segments=True)
    assert_segmentlist_equal(segs.active, SEGMENTS)
