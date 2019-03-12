# -*- coding: utf-8 -*-
# Copyright (C) Alex Urban (2019)
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
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for `gwdetchar.scattering`
"""

import numpy
from numpy import testing as nptest

from gwpy.timeseries import TimeSeries

from .. import scattering

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

TWOPI = 2*numpy.pi
TIMES = numpy.arange(0, 1, 1./2048)
OPTIC = TimeSeries(numpy.cos(TWOPI*10*TIMES), sample_rate=2048)


# -- make sure plots run end-to-end -------------------------------------------

def test_get_fringe_frequency():
    # calculate the fringe frequency
    fringef = scattering.get_fringe_frequency(OPTIC, multiplier=1)
    assert str(fringef.unit) == 'Hz'
    assert fringef.sample_rate.value == OPTIC.sample_rate.value
    assert fringef.size == OPTIC.size - 1
    nptest.assert_almost_equal(
        fringef.value.max() * (1.064 / 2) / TWOPI, 10, decimal=2)
