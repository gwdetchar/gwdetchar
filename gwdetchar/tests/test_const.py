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

import argparse
import os

import pytest

from .. import (cli, const as _const)

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
