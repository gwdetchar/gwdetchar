# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Tests for `gwdetchar.vetdef.ligolw_vetodef_append`
"""

import os
from unittest import mock
from ..ligolw_vetodef_create import main as create_cli
from ..ligolw_vetodef_append import main as append_cli
from gwpy.segments import DataQualityFlag

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'

FLAG = DataQualityFlag(known=[(123456788, 123456789)],
                       name='X1:DCH-TEST_FLAG:1')


@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG)
def test_ligolw_vetodef_append(flag):
    args = [
        'X1-TEST-123456789-1.xml',
        '--ifos', 'H1,L1',
    ]
    create_cli(args)

    args = [
        'X1-TEST-123456789-1.xml',
        'X1:DCH-TEST_FLAG:1',
        '--use-database-metadata',
        '--comment', 'This is a test comment',
    ]
    append_cli(args)

    os.remove('X1-TEST-123456789-1.xml')


@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG)
def test_ligolw_vetodef_append_fail(flag):
    args = [
        'X1-TEST-123456789-1.xml',
        '--ifos', 'H1,L1',
    ]
    create_cli(args)

    args = [
        'X1-TEST-123456789-1.xml',
        'X1:DCH-TEST_FLAG',
        '--use-database-metadata',
        '--comment', 'This is a test comment',
    ]
    try:
        append_cli(args)
    except AttributeError as e:
        assert e.args[0] == (
            "Failed to parse X1:DCH-TEST_FLAG as <ifo>:<name>:<version>"
        )
    else:
        assert False

    os.remove('X1-TEST-123456789-1.xml')
