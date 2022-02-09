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

"""Tests for `gwdetchar.omega.plot`
"""

import os
import shutil
import tempfile

import numpy
from scipy import signal

from gwpy.timeseries import TimeSeries

from .. import (config, core)

from matplotlib import use
use('agg')  # noqa

# backend-dependent import
from .. import plot  # noqa: E402

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

FFTLENGTH = 8

NOISE = TimeSeries(
    numpy.random.normal(loc=1, scale=.5, size=16384 * 68),
    sample_rate=16384, epoch=-34).zpk([], [0], 1)
GLITCH = TimeSeries(
    signal.gausspulse(numpy.arange(-1, 1, 1./16384), bw=100),
    sample_rate=16384, epoch=-1) * 1e-4
INPUT = NOISE.inject(GLITCH)

CONFIGURATION = {
    'q-range': '3.3166,150',
    'frequency-range': '4.0,Inf',
    'plot-time-durations': '4',
    'always-plot': 'True',
}
CHANNEL = config.OmegaChannel(
    channelname='L1:TEST-STRAIN', section='test', **CONFIGURATION)

SERIES = core.scan(
    gps=0, channel=CHANNEL, xoft=INPUT, resample=2048, fftlength=FFTLENGTH)
XOFT, _, _, QGRAM, _, QSPEC, _ = SERIES


# -- make sure plots run end-to-end -------------------------------------------

def test_timeseries_plot():
    with tempfile.NamedTemporaryFile(suffix='.png') as png:
        plot.timeseries_plot(XOFT, gps=0, span=4, channel=CHANNEL.name,
                             output=png, ylabel='Test')


def test_spectrogram_plot():
    with tempfile.NamedTemporaryFile(suffix='.png') as png:
        plot.spectral_plot(
            QSPEC, gps=0, span=4, channel=CHANNEL.name, output=png)


def test_qgram_plot():
    with tempfile.NamedTemporaryFile(suffix='.png') as png:
        plot.spectral_plot(QGRAM.table(), gps=0, span=4,
                           channel=CHANNEL.name, output=png)


def test_write_qscan_plots(tmpdir):
    tmpdir.mkdir('plots')
    wdir = str(tmpdir)
    os.chdir(wdir)
    plot.write_qscan_plots(gps=0, channel=CHANNEL, series=SERIES)
    shutil.rmtree(wdir, ignore_errors=True)
