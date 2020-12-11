# -*- coding: utf-8 -*-
# Copyright (C) Alex Urban (2020)
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

"""Tests for the `gwdetchar.omega` command-line interface
"""

import os
import numpy
import pytest
import shutil

from scipy.signal import gausspulse
from unittest import mock

from gwpy.segments import (
    Segment,
    SegmentList,
    DataQualityFlag,
)
from gwpy.timeseries import (
    TimeSeries,
    TimeSeriesDict,
)

from .. import __main__ as omega_cli

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

# -- test configurations

K1_CONFIG = u"""[primary]
f-low = 10.0
source = {path}
duration = 32
fftlength = 8
matched-filter-length = 6
channel = K1:GW-PRIMARY_CHANNEL

[GW]
name = Gravitational Wave Strain
q-range = 3.3166,150.0
frequency-range = 10.0,1024.0
source = {path}
state-flag = K1:DCH-TEST_FLAG:1
duration = 32
fftlength = 8
max-mismatch = 0.2
snr-threshold = 5
always-plot = True
plot-time-durations = 1,4,16
channels = K1:GW-PRIMARY_CHANNEL

[AUX]
name = Auxiliary Sensors
q-range = 3.3166,100.0
frequency-range = 4.0,1024.0
source = {path}
state-flag = K1:DCH-TEST_FLAG:1
duration = 32
fftlength = 8
max-mismatch = 0.35
snr-threshold = 5.5
always-plot = False
plot-time-durations = 1,4,16
channels = K1:AUX-HIGH_SIGNIFICANCE
    K1:AUX-LOW_SIGNIFICANCE
    K1:AUX-INVALID_DATA
""".rstrip()

NETWORK_CONFIG = u"""[H1]
name = LIGO-Hanford
q-range = 3.3166,150.0
frequency-range = 10.0,1024.0
source = {path}
duration = 32
fftlength = 8
max-mismatch = 0.2
snr-threshold = 5
always-plot = True
plot-time-durations = 1,4,16
channels = H1:GW-PRIMARY_CHANNEL

[L1]
name = LIGO-Livingston
q-range = 3.3166,150.0
frequency-range = 10.0,1024.0
source = {path}
duration = 32
fftlength = 8
max-mismatch = 0.2
snr-threshold = 5
always-plot = True
plot-time-durations = 1,4,16
channels = L1:GW-PRIMARY_CHANNEL
""".rstrip()

NETWORK_CONFIG_WITH_PRIMARY = """[primary]
f-low = 10.0
source = {path}
duration = 32
fftlength = 8
matched-filter-length = 6
channel = L1:GW-PRIMARY_CHANNEL

""" + NETWORK_CONFIG

MOCK_SUMMARY = """Channel,Central Time,Central Frequency (Hz),Q,Energy,SNR,Correlation,Standard Deviation,Delay (ms)
H1:GW-PRIMARY_CHANNEL,17.0,69.0,8.6,3021.39990234375,77.7,3.5,1.224587425297728,-50
L1:GW-PRIMARY_CHANNEL,17.0,78.6,8.6,31.200000762939453,7.9,6.3,1.3387611859727206,19
K1:GW-PRIMARY_CHANNEL,17.0,88.0,8.6,70.9000015258789,11.9,221.9,16.73187955362334,0
K1:AUX-HIGH_SIGNIFICANCE,17.0,62.4,8.6,43.400001525878906,9.3,6.9,1.7532027279924842,-50
K1:AUX-LOW_SIGNIFICANCE,17.0,102.7,44.2,33.79999923706055,8.2,13.7,4.709735874989297,2
K1:AUX-INVALID_DATA,17.0,103.0,69.0,103.5999984741211,14.4,5.0,1.445966601520126,-55
"""  # noqa: E501

# -- test data

GPS = 17

SIGNAL = TimeSeries(
    gausspulse(numpy.arange(-1, 1, 1./4096), bw=100),
    sample_rate=4096,
    epoch=GPS - 1,
)

TEST_FLAG = DataQualityFlag(
    name="K1:DCH-TEST_FLAG:1",
    active=SegmentList(),
    known=SegmentList([Segment(0, 34)]),
)

K1_DATA = TimeSeriesDict({
    "K1:GW-PRIMARY_CHANNEL": TimeSeries(
        numpy.random.normal(loc=1, scale=.5, size=4096 * GPS * 2),
        sample_rate=4096,
        epoch=0,
    ).zpk([], [0], 1).inject(SIGNAL),
    "K1:AUX-HIGH_SIGNIFICANCE": TimeSeries(
        numpy.random.normal(loc=1, scale=.5, size=4096 * GPS * 2),
        sample_rate=4096,
        epoch=0,
    ).zpk([], [0], 1).inject(SIGNAL),
    "K1:AUX-LOW_SIGNIFICANCE": TimeSeries(
        numpy.random.normal(loc=1, scale=.5, size=4096 * GPS * 2),
        sample_rate=4096,
        epoch=0,
    ),
    "K1:AUX-INVALID_DATA": TimeSeries(
        numpy.full(4096 * GPS * 2, numpy.nan),
        sample_rate=4096,
        epoch=0,
    ),
})

NETWORK_DATA = TimeSeriesDict({
    "H1:GW-PRIMARY_CHANNEL": TimeSeries(
        numpy.random.normal(loc=1, scale=.5, size=4096 * GPS * 2),
        sample_rate=4096,
        epoch=0,
    ).zpk([], [0], 1).inject(SIGNAL),
    "L1:GW-PRIMARY_CHANNEL": TimeSeries(
        numpy.random.normal(loc=1, scale=.5, size=4096 * GPS * 2),
        sample_rate=4096,
        epoch=0,
    ).zpk([], [0], 1).inject(SIGNAL),
})


# -- utils --------------------------------------------------------------------

def _get_inputs(workdir, config, data):
    """Prepare and return paths to input data products for Omega scan testing
    """
    # get path to data files
    ini_target = os.path.join(workdir, "config.ini")
    data_target = os.path.abspath(os.path.join(workdir, "data.h5"))
    # write to data files and return
    with open(ini_target, 'w') as f:
        f.write(config.format(path=data_target))
    data.write(data_target, format="hdf5", overwrite=True)
    return ini_target


# -- cli tests ----------------------------------------------------------------

def test_main_single_ifo(caplog, tmpdir):
    outdir = str(tmpdir)
    ini_source = _get_inputs(outdir, K1_CONFIG, K1_DATA)
    args = [
        str(GPS),
        '--ifo', 'K1',
        '--config-file', ini_source,
        '--output-dir', outdir,
        '--ignore-state-flags',
    ]
    # test from scratch
    with pytest.warns(UserWarning) as record:
        omega_cli.main(args)
    assert 'K1 Omega Scan {:.1f}'.format(GPS) in caplog.text
    assert caplog.text.count('Channel not significant') == 1
    assert os.path.isfile(os.path.join(outdir, 'index.html'))
    assert os.path.isfile(os.path.join(outdir, 'data', 'summary.csv'))
    assert 'array must not contain infs or NaNs' in record[-1].message.args[0]
    # test with checkpointing
    caplog.clear()
    with pytest.warns(UserWarning) as record:
        omega_cli.main(args)
    assert caplog.text.count('Checkpointing from {}'.format(outdir)) == 1
    assert caplog.text.count('Checkpointing K1:GW-PRIMARY_CHANNEL '
                             'from a previous run') == 1
    assert caplog.text.count('Checkpointing K1:AUX-HIGH_SIGNIFICANCE '
                             'from a previous run') == 1
    assert caplog.text.count('Channel not significant') == 1
    assert 'array must not contain infs or NaNs' in record[-1].message.args[0]
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)


def test_main_multi_ifo(caplog, tmpdir):
    outdir = str(tmpdir)
    ini_source = _get_inputs(outdir, NETWORK_CONFIG, NETWORK_DATA)
    args = [
        str(GPS),
        '--ifo', 'Network',
        '--config-file', ini_source,
        '--output-dir', outdir,
    ]
    # test from scratch
    omega_cli.main(args)
    assert 'Network Omega Scan {}'.format(GPS) in caplog.text
    assert os.path.isfile(os.path.join(outdir, 'index.html'))
    assert os.path.isfile(os.path.join(outdir, 'data', 'summary.csv'))
    # test with checkpointing and --disable-correlation
    ini_source = _get_inputs(
        outdir, NETWORK_CONFIG_WITH_PRIMARY, NETWORK_DATA)
    omega_cli.main(args + ['--disable-correlation'])
    assert 'Checkpointing from {}'.format(outdir) in caplog.text
    # test with checkpointing that expects cross-correlation
    with pytest.raises(KeyError) as exc:
        omega_cli.main(args)
    assert 'Cross-correlation is not available from this record' in str(exc)
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)


@mock.patch('gwpy.segments.DataQualityFlag.query',
            return_value=TEST_FLAG)
def test_main_inactive_segments(segserver, caplog):
    outdir = 'null-test'
    # write input data products to current working directory
    # this is done to test Omega scans' relative path construction
    ini_source = _get_inputs(os.path.curdir, K1_CONFIG, K1_DATA)
    args = [
        str(GPS),
        '--ifo', 'K1',
        '--config-file', ini_source,
        '--output-dir', outdir,
    ]
    omega_cli.main(args)
    # test output
    assert 'Finalizing HTML at {}'.format(
        os.path.abspath(outdir)) in caplog.text
    with open(os.path.join(outdir, "index.html"), 'r') as f:
        assert ('No significant channels found during '
                'active analysis segments') in f.read()
    # clean up
    os.remove('config.ini')
    os.remove('data.h5')
    shutil.rmtree(outdir, ignore_errors=True)


def test_main_invalid_config_files():
    ini_source = '/does/not/exist.ini'
    args = [
        str(GPS),
        '--ifo', 'V1',
        '--config-file', ini_source,
    ]
    # test that a non-existing configuration file raises OSError
    with pytest.raises(OSError) as exc:
        omega_cli.main(args)
    assert str(exc.value) == "Cannot read file '{}'".format(ini_source)


def test_main_multiple_config_files(tmpdir):
    outdir = str(tmpdir)
    os.mkdir(os.path.join(outdir, 'data'))
    ini1 = _get_inputs(outdir, K1_CONFIG, K1_DATA)
    ini2 = os.path.join(outdir, 'network-config.ini')
    with open(ini2, 'w') as f:
        f.write(K1_CONFIG.format(path='data.h5'))
    with open(os.path.join(outdir, 'data', 'summary.csv'), 'w') as f:
        f.write(MOCK_SUMMARY)
    args = [
        str(GPS),
        '--ifo', 'Network',
        '--config-file', ini1,
        '--config-file', ini2,
        '--output-dir', outdir,
        '--ignore-state-flags',
    ]
    # test output
    omega_cli.main(args)
    assert os.path.exists(os.path.join(outdir, 'index.html'))
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
