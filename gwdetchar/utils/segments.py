# coding=utf-8
# Copyright (C) Evan Goetz (2025)
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

from gwdatafind import find_urls
from gwdatafind.utils import file_segment
from gwpy.segments import (
    Segment,
    SegmentList,
)


def intersection_data_segs(dq_segs, site, frametype, **kwargs):
    """Get segment list containing the intersection of some segment list,
    typically the data quality segments, with segment list of available data;
    avoids problems of data availability

    Parameters
    ----------
    dq_segs : `~gwpy.segments.SegmentList`
        Segments from data quality flags

    site : `str`
        single-character name of site to match

    frametype : `str`
        name of dataset to match

    Returns
    -------
    intersection : `~gwpy.segments.SegmentList`
        Segments from the intersection of data quality flags and data
        availability
    """
    # Loop over data quality segments getting frame files for each segment
    data_segs = SegmentList()
    for seg in dq_segs:
        cache = find_urls(site, frametype, seg[0], seg[1], **kwargs)
        for fr in cache:
            data_segs.append(Segment(file_segment(fr)))

    # Coalesce the segments
    data_segs.coalesce()

    # take the intersection of the data quality segments with the data
    # available segments
    intersection = dq_segs & data_segs

    return intersection
