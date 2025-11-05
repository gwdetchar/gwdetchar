# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Tests for `gwdetchar.vetdef.ligolw_vetodef_validate`
"""

import os
import unittest
from unittest import mock
from gwpy.segments import DataQualityFlag
from ..ligolw_vetodef_create import main as create_cli
from ..ligolw_vetodef_append import main as append_cli
from ..ligolw_vetodef_validate import main as validate_cli

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'

FLAG = DataQualityFlag(known=[(123456789, 123456790)],
                       name='X1:DCH-TEST_FLAG:1')


@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG)
def test_ligolw_vetodef_validate(flag):
    args = [
        'X1-TEST-123456789-1.xml',
        '--ifos', 'H1,L1',
    ]
    create_cli(args)

    args = [
        'X1-TEST-123456789-1.xml',
        'X1:DCH-TEST_FLAG:1',
        '--start-time', '123456789',
        '--end-time', '123456790',
        '--comment', 'This is a test comment',
    ]
    append_cli(args)

    args = [
        'X1-TEST-123456789-1.xml',
        '--verbose'
    ]
    validate_cli(args)

    os.remove('X1-TEST-123456789-1.xml')


@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG)
class TestLigolwVetodefValidateFail(unittest.TestCase):

    def setUp(self):
        args = [
            'X1-TEST-123456789-1.xml',
            '--ifos', 'H1,L1',
        ]
        create_cli(args)

        args = [
            'X1-TEST-123456789-1.xml',
            'X1:DCH-TEST_FLAG:1',
            '--start-time', '123456789',
            '--end-time', '123456790',
            '--comment', 'This is a test comment',
            '--force',
        ]
        append_cli(args)
        append_cli(args)

    def tearDown(self):
        os.remove('X1-TEST-123456789-1.xml')

    def test_raise_assertion_error(self, flag):
        args = [
            'X1-TEST-123456789-1.xml',
            '--verbose',
        ]
        with self.assertRaises(AssertionError):
            validate_cli(args)

    def test_exit(self, flag):
        args = [
            'X1-TEST-123456789-1.xml',
            '--verbose',
            '--test-all',
        ]
        with self.assertRaises(SystemExit):
            validate_cli(args)
