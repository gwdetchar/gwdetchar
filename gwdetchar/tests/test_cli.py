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

"""Test suite for `gwdetchar.cli`
"""

import logging
import argparse
try:
    from importlib import reload
except ImportError:  # python < 3
    reload = reload

import pytest

from .. import (cli, __version__ as gwdetchar_version, const as _const)


def test_logger():
    logger = cli.logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'gwdetchar.cli'
    assert logger.level == logging.DEBUG


@pytest.fixture
def const():
    yield _const
    reload(_const)


@pytest.fixture
def parser():
    return argparse.ArgumentParser()


def test_create_parser():
    parser = cli.create_parser(description=__doc__)
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.description == __doc__
    assert parser._actions[-1].version == gwdetchar_version


@pytest.mark.parametrize('inv, outv', [
    (None, gwdetchar_version),
    ('test', 'test'),
])
def test_add_version_option(parser, inv, outv):
    act = cli.add_version_option(parser, version=inv)
    assert act.version == outv
    with pytest.raises(SystemExit):
        parser.parse_args(['--version'])


@pytest.mark.parametrize('ifo', (_const.IFO, None))
def add_ifo_option(parser, const, ifo):
    const.IFO == ifo
    parser.add_ifo_option()
    args = parser.parse_args([])
    assert args.ifo == ifo
    if ifo is None:
        with pytest.raises(argparse.ArgumentError):
            parser.parse_args([])
    assert parser.parse_args(['--ifo', 'test']).ifo == 'test'


def test_add_gps_start_stop_arguments(parser):
    cli.add_gps_start_stop_arguments(parser)
    args = parser.parse_args(['Jan 1 2000', 'Jan 2 2000'])
    assert args.gpsstart == 630720013
    assert args.gpsend == 630806413


def test_add_gps_start_stop_options(parser):
    cli.add_gps_start_stop_options(parser)
    args = parser.parse_args([])
    assert args.gps_start_time is None
    assert args.gps_end_time is None
    args = parser.parse_args(['-s', 'Jan 1 2000',
                              '--gps-end-time', 'Jan 2 2000'])
    assert args.gps_start_time == 630720013
    assert args.gps_end_time == 630806413


def test_add_frame_type_name(parser):
    cli.add_frametype_option(parser)
    args = parser.parse_args(['--frametype', 'test'])
    assert args.frametype == 'test'


def test_add_nproc_option(parser):
    cli.add_nproc_option(parser)
    assert parser.parse_args([]).nproc == 8
    assert parser.parse_args(['-j', '2']).nproc == 2
