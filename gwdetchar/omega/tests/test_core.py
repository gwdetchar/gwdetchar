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

"""Tests for `gwdetchar.omega.core`
"""

import numpy
from numpy import testing as nptest
from scipy import signal

from gwpy.timeseries import TimeSeries
from gwpy.signal.qtransform import QGram
from gwpy.spectrogram import Spectrogram

from .. import (core, config)

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
    channelname='X1:TEST-STRAIN', section='test', **CONFIGURATION)


# -- unit tests ---------------------------------------------------------------

def test_highpass():
    # high-pass filter the input
    hp = core.highpass(INPUT, f_low=4)
    assert INPUT.is_compatible(hp)
    assert hp.size == INPUT.size
    assert abs(INPUT.value.mean()) > 10
    nptest.assert_almost_equal(hp.value.mean(), 0, decimal=5)


def test_whiten():
    # whiten the input
    whitened = core.whiten(INPUT, fftlength=FFTLENGTH)
    assert INPUT.is_compatible(whitened)
    assert whitened.size == INPUT.size

    # test the whitened timeseries with the glitch cropped out
    ind = list(range(33 * 16384)) + list(range(35 * 16384, whitened.size))
    nptest.assert_almost_equal(whitened.value[ind].mean(), 0, decimal=4)
    nptest.assert_almost_equal(whitened.value[ind].std(), 1, decimal=1)

    # test that the peak occurs at the expected time
    tmax = whitened.times[whitened.argmax()]
    assert tmax.value == 0


def test_conditioner():
    # get conditioned data products
    wxoft, xoft = core.conditioner(INPUT, fftlength=FFTLENGTH, resample=4096)
    assert isinstance(wxoft, TimeSeries)
    assert isinstance(xoft, TimeSeries)
    assert xoft.sample_rate.value == 4096
    assert xoft.is_compatible(wxoft)


def test_conditioner_with_highpass():
    # get conditioned data with highpassing
    wxoft, hpxoft, xoft = core.conditioner(
        INPUT, fftlength=FFTLENGTH, resample=4096, f_low=4)
    assert isinstance(wxoft, TimeSeries)
    assert isinstance(hpxoft, TimeSeries)
    assert xoft.is_compatible(wxoft)
    assert xoft.is_compatible(hpxoft)
    nptest.assert_almost_equal(hpxoft.value.mean(), 0, decimal=5)
    nptest.assert_almost_equal(wxoft.value.mean(), 0, decimal=2)


def test_primary():
    # condition a data stream for use as a matched-filter
    length = 6
    mfilter = core.primary(0, length=length, hoft=INPUT, fftlength=FFTLENGTH)
    assert mfilter.duration.value == length
    assert mfilter.times[mfilter.argmax()].value == 0

    # test again, with a high-pass filter
    f_low = 4
    mfilterhp = core.primary(0, length=length, f_low=f_low, hoft=INPUT,
                             fftlength=FFTLENGTH)
    assert mfilterhp.duration.value == length
    assert mfilterhp.times[mfilterhp.argmax()].value == 0


def test_cross_correlate():
    # cross-correlate two data streams
    wxoft = core.whiten(INPUT, fftlength=FFTLENGTH)
    whoft = core.primary(0, length=6, hoft=INPUT, fftlength=FFTLENGTH)
    corr = core.cross_correlate(wxoft, whoft)
    assert wxoft.is_compatible(corr)
    tmax = corr.abs().times[corr.argmax()]
    assert tmax.value == 0

    # test with resampling
    corr2 = core.cross_correlate(wxoft.resample(2048), whoft)
    corr3 = core.cross_correlate(wxoft, whoft.resample(2048))
    assert corr2.sample_rate.value == 2048
    assert corr2.is_compatible(corr3)
    assert corr2.abs().times[corr2.argmax()].value == tmax.value
    assert corr3.abs().times[corr3.argmax()].value == tmax.value


def test_scan():
    # get omega scan products
    xoft, hpxoft, wxoft, qgram, rqgram, qspec, rqspec = core.scan(
        gps=0, channel=CHANNEL, xoft=INPUT, resample=2048, fftlength=FFTLENGTH)
    assert isinstance(xoft, TimeSeries)
    assert isinstance(hpxoft, TimeSeries)
    assert isinstance(wxoft, TimeSeries)
    assert isinstance(qgram, QGram)
    assert isinstance(rqgram, QGram)
    assert isinstance(qspec, Spectrogram)
    assert isinstance(rqspec, Spectrogram)

    # test features
    assert qspec.shape == (1400, 700)
    assert qspec.shape == rqspec.shape
    assert qspec.q == rqspec.q
    assert qspec.q == qgram.plane.q
    assert qgram.plane.q == rqgram.plane.q

    # test low false alarm rate
    CHANNEL.always_plot = False
    empty = core.scan(gps=0, channel=CHANNEL, xoft=NOISE, resample=2048,
                      fftlength=FFTLENGTH)
    assert empty is None
