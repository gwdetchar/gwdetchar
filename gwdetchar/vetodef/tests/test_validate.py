# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Tests for `gwdetchar.vetdef.validate`
"""

import os
from igwn_ligolw.lsctables import VetoDef, VetoDefTable
from gwpy.segments import DataQualityFlag

from unittest import mock

from .. import validate

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'


VETO = VetoDef(
    category=1,
    comment="Test",
    end_pad=1,
    end_time=1393286418,
    ifo="X1",
    name="Veto",
    process_id=1234,
    start_pad=0,
    start_time=1393200018,
    version=1,
)
VETOTABLE = VetoDefTable()
VETOTABLE.append(VETO)
FLAG = DataQualityFlag(known=[(-33, 33)], active=[(-33, 33)],
                       name='X1:TEST-FLAG:1')


def test_check_veto_def_times():
    validate.check_veto_def_times(VETO)


def test_check_veto_def_padding():
    validate.check_veto_def_padding(VETO)


@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG)
def test_check_veto_def_exists(flag):
    validate.check_veto_def_exists(VETO)


@mock.patch.dict(os.environ, {'VETODEF_ERROR_ACTION': 'warn'})
@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=FLAG,
            side_effect=RuntimeError)
def test_check_veto_def_exists_invalid(flag):
    validate.check_veto_def_exists(VETO)


def test_check_veto_def_category():
    validate.check_veto_def_category(VETO)


def test_check_veto_table_versions():
    validate.check_veto_table_versions(VETOTABLE)


def test_check_veto_table_overlap():
    validate.check_veto_table_overlap(VETOTABLE)
