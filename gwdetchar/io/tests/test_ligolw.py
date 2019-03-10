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

"""Tests for `gwdetchar.io.ligolw`
"""

import pytest

import numpy
from numpy.testing import (assert_array_equal, assert_allclose)

from gwpy.segments import (Segment, SegmentList)
from gwpy.testing.utils import assert_segmentlist_equal

lsctables = pytest.importorskip("glue.ligolw.lsctables")
ligolw = pytest.importorskip("gwdetchar.io.ligolw")


def test_new_table():
    tab = ligolw.new_table('sngl_burst')
    assert isinstance(tab, lsctables.SnglBurstTable)
    assert sorted(tab.columnnames) == sorted(
        lsctables.SnglBurstTable.validcolumns.keys())

    cols = ['peak_time', 'peak_time_ns', 'snr']
    tab = ligolw.new_table(lsctables.SnglBurstTable, columns=cols)
    assert tab.columnnames == cols


def test_sngl_burst_from_times():
    numpy.random.seed(0)
    times = numpy.random.random(4) * 100.
    tab = ligolw.sngl_burst_from_times(times)
    assert isinstance(tab, lsctables.SnglBurstTable)
    assert len(tab) == 4
    nanosec, sec = numpy.modf(times)
    assert_array_equal(tab.getColumnByName('peak_time').asarray(), sec)
    assert_allclose(tab.getColumnByName('peak_time_ns').asarray(),
                    nanosec * 1e9)


def test_segments_from_sngl_burst():
    tab = ligolw.sngl_burst_from_times([1, 4, 7, 10], channel='test')
    segs = ligolw.segments_from_sngl_burst(tab, 1)
    assert_segmentlist_equal(segs['test'].active, SegmentList([
        Segment(0, 2), Segment(3, 5), Segment(6, 8), Segment(9, 11),
    ]))


def test_table_to_document():
    from glue.ligolw.ligolw import Document
    tab = ligolw.new_table('sngl_burst')
    xmldoc = ligolw.table_to_document(tab)
    assert isinstance(xmldoc, Document)
    assert xmldoc.childNodes[-1].childNodes[0] is tab
