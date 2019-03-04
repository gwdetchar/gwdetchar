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

"""Test suite for `gwdetchar.const`
"""

import os

try:
    from importlib import reload
except ImportError:  # python < 3
    reload = reload

import pytest

from .. import const as _const

_DEFAULT_ENV = os.environ.copy()


@pytest.fixture
def const():
    yield _const
    reload(_const)
    os.environ.update(_DEFAULT_ENV)


@pytest.mark.parametrize('env', [
    {},
    {'IFO': 'X1'},
])
def test_const(const, env):
    os.environ.update(env)
    reload(const)
    if env:
        assert const.IFO == env['IFO']
        assert const.ifo == const.IFO.lower()
    else:
        assert const.IFO is None
        assert const.ifo is None
    assert const.site is None


@pytest.mark.parametrize('gps, default, epoch', [
    (1126259462, None, 'ER8'),
    (1187008882.43, None, 'O2'),
    (-1, 'test', 'test'),
])
def test_gps_epoch(gps, default, epoch):
    assert _const.gps_epoch(gps, default=default) == epoch


def test_gps_epoch_valueerror():
    with pytest.raises(ValueError):
        _const.gps_epoch(-1, default=None)


def test_latest_epoch(const):
    const.EPOCH = {
        'test1': (0, 10),
        'test2': (10, 20),
    }
    assert const.latest_epoch() == 'test2'
