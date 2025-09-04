# -*- coding: utf-8 -*-
# Copyright (C) Evan Goetz (2025)
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

"""Tests for :mod:`gwdetchar.utils.segments`
"""

from unittest import mock

from gwpy.segments import Segment, SegmentList

from .. import segments

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'


DQSEGS = SegmentList([Segment(0, 10), Segment(20, 30)])
DATASEGS = SegmentList([Segment(0, 8), Segment(18, 35)])
INTERSECTION = DQSEGS & DATASEGS
URLS = ['H-H1_R-0-8.gwf', 'H-H1_R-18-17.gwf']


@mock.patch('gwdetchar.utils.segments.find_urls', return_value=URLS)
@mock.patch.dict('os.environ', {'GWDATAFIND_SERVER': 'test:80'})
def test_intersection_data_segs(segs):
    assert segments.intersection_data_segs(
        DQSEGS, 'H', 'H1_R') == INTERSECTION
