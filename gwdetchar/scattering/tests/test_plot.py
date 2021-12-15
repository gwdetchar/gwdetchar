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

"""Tests for `gwdetchar.scattering.plot`
"""

import os
import numpy
import shutil

from gwpy.timeseries import TimeSeries

from matplotlib import use
use('Agg')

# backend-dependent import
from .. import plot  # noqa: E402

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

TWOPI = 2 * numpy.pi
TIMES = numpy.arange(0, 16384 * 64)
NOISE = TimeSeries(
    numpy.random.normal(loc=1, scale=.5, size=16384 * 64),
    sample_rate=16384, epoch=-32).zpk([], [0], 1)
FRINGE = TimeSeries(
    numpy.cos(TWOPI * TIMES), sample_rate=16384, epoch=-32)
DATA = NOISE.inject(FRINGE)
QSPECGRAM = DATA.q_transform(logf=True, method="median")


# -- make sure plots run end-to-end -------------------------------------------

def test_spectral_comparison(tmpdir):
    outdir = str(tmpdir)
    plot1 = os.path.join(outdir, 'test1.png')
    plot2 = os.path.join(outdir, 'test2.png')
    # test plotting
    plot.spectral_comparison(0, QSPECGRAM, FRINGE, plot1)
    plot.spectral_overlay(0, QSPECGRAM, FRINGE, plot2)
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
