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

"""Tests for `gwdetchar.omega.config`
"""

import os
from io import StringIO

import numpy
from scipy import signal

from gwpy.table import Table
from gwpy.timeseries import TimeSeries

from .. import (config, core)
from ...io.html import FancyPlot

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

CONFIGURATION = u"""
[primary]
; the primary channel, which will be used as a matched-filter
f-low = 4.0
resample = 4096
frametype = X1_HOFT
duration = 64
fftlength = 8
matched-filter-length = 6
channel = X1:TEST-STRAIN

[GW]
; name of this block, which contains h(t)
name = Gravitational Wave Strain
q-range = 3.3166,150.0
frequency-range = 4.0,1024
resample = 4096
frametype = X1_HOFT
state-flag = X1:OBSERVING:1
duration = 64
fftlength = 8
max-mismatch = 0.2
snr-threshold = 5
always-plot = True
plot-time-durations = 4
channels = X1:TEST-STRAIN
"""
CONFIG_FILE = StringIO(CONFIGURATION)

CP = config.OmegaConfigParser(ifo='X1')
CP.read_file(CONFIG_FILE)
BLOCKS = CP.get_channel_blocks()
PRIMARY = BLOCKS['primary']
GW = BLOCKS['GW']

ROWS = [[0]] * 8
COLS = ('Q', 'Energy', 'SNR', 'Central Time', 'Central Frequency (Hz)',
        'Correlation', 'Standard Deviation', 'Delay (ms)')
TABLE = Table(ROWS, names=COLS)


# -- test utilities -----------------------------------------------------------

def test_get_default_configuration():
    cfile = config.get_default_configuration(ifo='X1', gpstime=1126259462)
    assert cfile == [os.path.expanduser(
        '~detchar/etc/omega/ER8/X-X1_R-selected.ini')]
    nfile = config.get_default_configuration(ifo='Network', gpstime=1187008882)
    assert nfile == [os.path.expanduser('~detchar/etc/omega/O2/Network.ini')]


def test_get_fancyplots():
    fp = config.get_fancyplots(
        channel='X1:TEST-STRAIN', plottype='test-plot', duration=4)
    fname = 'plots/X1-TEST_STRAIN-test-plot-4.png'
    assert isinstance(fp, FancyPlot)
    assert fp.img == fname
    assert str(fp) == fp.img
    assert fp.caption == os.path.basename(fname)


def test_config_parser():
    # basic tests
    assert isinstance(CP, config.OmegaConfigParser)
    assert CP.sections() == ['primary', 'GW']

    # test primary section params
    assert CP.get('primary', 'f-low') == '4.0'
    assert CP.get('primary', 'resample') == '4096'
    assert CP.get('primary', 'frametype') == 'X1_HOFT'
    assert CP.get('primary', 'duration') == '64'
    assert CP.get('primary', 'fftlength') == '8'
    assert CP.get('primary', 'matched-filter-length') == '6'
    assert CP.get('primary', 'channel') == 'X1:TEST-STRAIN'

    # test GW section params
    assert CP.get('GW', 'name') == 'Gravitational Wave Strain'
    assert CP.get('GW', 'q-range') == '3.3166,150.0'
    assert CP.get('GW', 'frequency-range') == '4.0,1024'
    assert CP.get('GW', 'resample') == '4096'
    assert CP.get('GW', 'frametype') == 'X1_HOFT'
    assert CP.get('GW', 'state-flag') == 'X1:OBSERVING:1'
    assert CP.get('GW', 'duration') == '64'
    assert CP.get('GW', 'fftlength') == '8'
    assert CP.get('GW', 'max-mismatch') == '0.2'
    assert CP.get('GW', 'snr-threshold') == '5'
    assert CP.get('GW', 'always-plot') == 'True'
    assert CP.get('GW', 'plot-time-durations') == '4'
    assert CP.get('GW', 'channels') == 'X1:TEST-STRAIN'


def test_omega_channel_list():
    # basic test
    assert isinstance(GW, config.OmegaChannelList)

    # test primary block
    assert PRIMARY.key == 'primary'
    assert PRIMARY.parent is None
    assert PRIMARY.name is None
    assert PRIMARY.duration == 64
    assert PRIMARY.fftlength == 8
    assert PRIMARY.resample == 4096
    assert PRIMARY.source is None
    assert PRIMARY.frametype == 'X1_HOFT'
    assert PRIMARY.length == 6
    assert PRIMARY.flow == 4.
    assert PRIMARY.channel == config.OmegaChannel(
        'X1:TEST-STRAIN', PRIMARY.key, **PRIMARY.params)

    # test GW block
    assert GW.key == 'GW'
    assert GW.parent is None
    assert GW.name == 'Gravitational Wave Strain'
    assert GW.duration == 64
    assert GW.fftlength == 8
    assert GW.resample == 4096
    assert GW.source is None
    assert GW.frametype == 'X1_HOFT'
    assert GW.flag == 'X1:OBSERVING:1'
    assert GW.search == 0.5
    assert GW.dt == 0.1
    assert GW.channels == [config.OmegaChannel(
        'X1:TEST-STRAIN', GW.key, **GW.params)]


def test_omega_channel():
    # basic test
    channel = GW.channels[0]
    assert isinstance(channel, config.OmegaChannel)

    # test attributes
    assert channel.section == 'GW'
    assert channel.name == 'X1:TEST-STRAIN'
    assert channel.frametype == 'X1_HOFT'
    assert channel.qrange == (3.3166, 150.0)
    assert channel.frange == (4.0, 1024)
    assert channel.mismatch == 0.2
    assert channel.snrthresh == 5
    assert channel.always_plot is True
    assert channel.pranges == [4]


def test_save_loudest_tile_features():
    # prepare input data
    channel = GW.channels[0]
    noise = TimeSeries(
        numpy.random.normal(loc=1, scale=.5, size=16384 * 68),
        sample_rate=16384, epoch=-34).zpk([], [0], 1)
    glitch = TimeSeries(
        signal.gausspulse(numpy.arange(-1, 1, 1./16384), bw=100),
        sample_rate=16384, epoch=-1) * 1e-4
    in_ = noise.inject(glitch)
    _, _, _, qgram, _, _, _ = core.scan(
        gps=0, channel=channel, xoft=in_, resample=4096, fftlength=8)

    # test loudest tiles
    channel.save_loudest_tile_features(qgram, correlate=glitch)
    assert channel.Q == numpy.around(qgram.plane.q, 1)
    assert channel.energy == numpy.around(qgram.peak['energy'], 1)
    assert channel.snr == numpy.around(qgram.peak['snr'], 1)
    assert channel.t == numpy.around(qgram.peak['time'], 3)
    assert channel.f == numpy.around(qgram.peak['frequency'], 1)
    assert channel.corr == numpy.around(glitch.max().value, 1)
    assert channel.delay == 0.0
    assert channel.stdev == glitch.std().value


def test_load_loudest_tile_features():
    channel = GW.channels[0]
    channel.load_loudest_tile_features(TABLE, correlated=True)
    assert channel.Q == 0
    assert channel.energy == 0
    assert channel.snr == 0
    assert channel.t == 0
    assert channel.f == 0
    assert channel.corr == 0
    assert channel.delay == 0
    assert channel.stdev == 0
