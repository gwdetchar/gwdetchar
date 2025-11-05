# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Tests for `gwdetchar.vetdef.ligolw_vetodef_create`
"""

import os
from ..ligolw_vetodef_create import main as create_cli

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'


def test_ligolw_vetodef_create():
    args = [
        'X1-TEST-123456789-1.xml',
        '--ifos', 'H1,L1',
    ]

    create_cli(args)
    os.remove('X1-TEST-123456789-1.xml')


def test_ligolw_vetodef_create_fail():
    args = [
        'X1-TEST-123456789-1.txt',
        '--ifos', 'H1,L1',
    ]
    try:
        create_cli(args)
    except ValueError as e:
        assert e.args[0] == (
            "Output filename must carry a `.xml` or `.xml.gz` extension"
        )
    else:
        assert False

    args = [
        'X1-TEST-123456789.xml',
        '--ifos', 'H1,L1',
    ]
    try:
        create_cli(args)
    except ValueError as e:
        assert e.args[0] == (
            'Output filename must follow the T050017 convention '
            '[https://dcc.ligo.org/LIGO-T050017]'
        )
    else:
        assert False
