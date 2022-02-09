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

"""Tests for the `gwdetchar.scattering.simple` command-line interface
"""

import os
import numpy
import shutil

from numpy.testing import assert_equal
from unittest import mock

from gwpy.timeseries import (
    TimeSeries,
    TimeSeriesDict,
)

from .. import simple

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

IFO = 'L1'

# -- test data

# The unit test below captures all use cases by simulating
#     (1) a missing optic channel, and
#     (2) a scattering fringe in h(t) predicted by only one optic.

DURATION = 68
FREQ = 1 / 10
SAMPLE = 4096

TIMES = numpy.arange(0, DURATION, 1 / SAMPLE)
PHASE = 42 * numpy.sin(2 * numpy.pi * FREQ * TIMES) / (2 * numpy.pi * FREQ)
SCATTER = TimeSeries(
    (numpy.sin(numpy.pi * TIMES / DURATION)
     * numpy.cos(2 * numpy.pi * PHASE)),
    sample_rate=SAMPLE,
)

HOFT = TimeSeries(
    numpy.random.normal(loc=1, scale=1.5, size=SCATTER.size),
    sample_rate=SAMPLE,
).inject(SCATTER.highpass(10))

AUX = TimeSeriesDict({
    ':'.join([IFO, chan]): TimeSeries(
        numpy.random.normal(loc=1, scale=1e-3, size=SCATTER.size),
        sample_rate=SAMPLE,
        name=':'.join([IFO, chan]),
    ).crop(4, 64) for chan in simple.MOTION_CHANNELS[1::]
})

PHASE = PHASE[4 * SAMPLE:-4 * SAMPLE]
AUX['{}:SUS-ITMX_R0_DAMP_L_IN1_DQ'.format(IFO)] += 1.064 * PHASE / 2


# -- cli tests ----------------------------------------------------------------

@mock.patch(
    'gwdetchar.scattering.simple._discover_data',
    return_value=(HOFT, AUX),
)
def test_main(data, caplog, tmpdir):
    outdir = str(tmpdir)
    args = [  # command-line arguments
        str(DURATION / 2),
        '-i', IFO,
        '--multipliers', '1',
        '--output-dir', outdir,
    ]
    # test command-line tool
    simple.main(args)
    assert 1 == caplog.text.count(
        "Skipping {}:SUS-BS_M1_DAMP_L_IN1_DQ".format(IFO))
    assert len(simple.MOTION_CHANNELS) - 2 == caplog.text.count(
        "No significant evidence of scattering found")
    assert 1 == caplog.text.count(
        "Plotting spectra and projected fringe frequencies")
    assert 1 == caplog.text.count("1 chanels plotted")
    # test output
    assert_equal(
        set(os.listdir(outdir)),
        {"{}-SUS_ITMX_R0_DAMP_L_IN1_DQ-34.0-60-comparison.png".format(IFO),
         "{}-SUS_ITMX_R0_DAMP_L_IN1_DQ-34.0-60-overlay.png".format(IFO)},
    )
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
