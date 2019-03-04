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

"""Tests for `gwdetchar.lasso.plot`
"""

import os
import shutil

import pytest

import numpy

from matplotlib import use
use('agg')

from gwpy.plot import Plot
from gwpy.timeseries import TimeSeries

from .. import plot

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

DATA = numpy.random.normal(loc=0, scale=1, size=24*60)
SERIES = TimeSeries(DATA, sample_rate=60, unit='Mpc', name='X1:TEST')


# -- make sure plots run end-to-end -------------------------------------------

def test_save_figure(tmpdir):
    base = str(tmpdir)
    fig = SERIES.plot()
    tsplot = plot.save_figure(fig, os.path.join(base, 'test.png'))
    assert tsplot == os.path.join(base, 'test.png')
    shutil.rmtree(base, ignore_errors=True)


def test_save_legend(tmpdir):
    base = str(tmpdir)
    fig = Plot()
    ax = fig.gca()
    ax.plot(SERIES, label=SERIES.name)
    tsplot = plot.save_legend(ax, os.path.join(base, 'test.png'))
    assert tsplot == os.path.join(base, 'test.png')
    shutil.rmtree(base, ignore_errors=True)
