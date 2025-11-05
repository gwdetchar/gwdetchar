# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Utilities to validate a veto_def entry
"""

import os
import warnings

from urllib.error import URLError

from gwpy import segments
from dqsegdb2.utils import get_default_host

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

DEFAULT_SEGMENT_SERVER = get_default_host()


def handle_error(exc, action=None):
    """Handle errors based on requested action
    """
    if action is None:
        action = os.getenv('VETODEF_ERROR_ACTION', 'raise')

    # handle errors
    if action == 'ignore':
        return
    elif action == 'warn':
        warnings.warn(str(exc))
    else:
        raise exc


# -- veto_def validation ------------------------------------------------------

MAXIMUM_PADDING = 1200
MAXIMUM_CATEGORY = 5


def check_veto_def_times(veto):
    """Assert veto start_time and end_time are sane
    """
    start = veto.start_time
    end = veto.end_time
    assert end == 0 or end > start, "end_time before start_time"
    assert start >= 0, "start_time negative"
    assert end >= 0, "end_time negative"
    assert start < 1e10, "start_time too big"
    assert end < 1e10, "end_time too big"


def check_veto_def_padding(veto):
    """Assert veto start_pad and end_pad are sane
    """
    start = veto.start_pad
    end = veto.end_pad
    assert start > -MAXIMUM_PADDING, "start_pad too big (negative)"
    assert start < MAXIMUM_PADDING, "start_pad too big (positive)"
    assert end > -MAXIMUM_PADDING, "end_pad too big (negative)"
    assert end < MAXIMUM_PADDING, "end_pad too big (positive)"


def check_veto_def_exists(veto, host=DEFAULT_SEGMENT_SERVER, on_error=None):
    """Assert veto flag exist in database for times given
    """
    flag = f"{veto.ifo}:{veto.name}:{veto.version}"
    try:
        _ = segments.DataQualityFlag.query(
            flag,
            veto.start_time,
            veto.end_time or 1e10,
            host=host,
        )
    except (URLError, RuntimeError) as e:
        if isinstance(e, URLError) and e.code == 404:
            raise AssertionError("Flag not found in database")
        e.args = (
            f"Failed to query {host} for {flag}: {str(e)}",
        )
        handle_error(e, action=on_error)


def check_veto_def_category(veto):
    """Assert veto category is sane
    """
    category = veto.category
    assert category > 0, "category less than 1"
    assert category <= MAXIMUM_CATEGORY, \
        f"category greater than {MAXIMUM_CATEGORY}"


VETO_TESTS = [val for (key, val) in locals().items() if
              key.startswith('check_veto_def')]


# -- veto_def_table validation ------------------------------------------------

def check_veto_table_versions(table):
    """Assert no two version of the same flag in the table
    """
    versions = dict()
    for veto in table:
        flag = (veto.ifo, veto.name, veto.version)
        # record information for cross tests
        try:
            versions[flag].add(veto.version)
        except KeyError:
            versions[flag] = set([veto.version])

    for flag in sorted(versions.keys()):
        assert len(versions[flag]) == 1, "multiple versions of flag"


def check_veto_table_overlap(table):
    """Assert no overlapping segments for the same (flag, version) in the table
    """
    segs = dict()
    for veto in table:
        flag = (veto.ifo, veto.name, veto.version)
        seg = segments.Segment(veto.start_time, veto.end_time or 1e10)
        try:
            assert not segs[flag].intersects_segment(seg), \
                   "overlapping segments for %s:%s:%d" % flag
        except KeyError:
            segs[flag] = segments.SegmentList([seg])
        else:
            segs[flag].append(seg)


TABLE_TESTS = [val for (key, val) in locals().items() if
               key.startswith('check_veto_table')]
