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

"""Tests for the `gwdetchar.scattering` command-line interface
"""

import os
import numpy
import shutil

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

from .. import __main__ as scattering_cli

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

IFO = 'H1'

# -- test data

# The unit test below captures all use cases by simulating
#     (1) a missing optic channel, and
#     (2) a scattering fringe in h(t) predicted by only one optic.

DURATION = 3608
FREQ = 1 / 10
SAMPLE = 4096

EMPTY_FLAG = DataQualityFlag(
    name="{}:DCH-TEST_FLAG:1".format(IFO),
    active=SegmentList([
        Segment(0, 25),
    ]),
    known=SegmentList([
        Segment(0, DURATION),
    ]),
)

TIMES = numpy.arange(0, DURATION, 1 / SAMPLE)
PHASE = 42 * numpy.sin(2 * numpy.pi * FREQ * TIMES) / (2 * numpy.pi * FREQ)
SCATTER = TimeSeries(
    (numpy.sin(numpy.pi * TIMES / DURATION)
     * numpy.cos(2 * numpy.pi * PHASE)),
    sample_rate=SAMPLE,
).highpass(10)

HOFT = TimeSeries(
    numpy.random.normal(loc=1, scale=1.5, size=SCATTER.size),
    sample_rate=SAMPLE,
).inject(SCATTER)

OSEMS = [chan for group in scattering_cli.OPTIC_MOTION_CHANNELS.values()
         for chan in group]
AUX = TimeSeriesDict({
    **{
        ':'.join([IFO, chan]): TimeSeries(
            numpy.random.normal(loc=1, scale=1e-3, size=SCATTER.size),
            sample_rate=SAMPLE,
            name=':'.join([IFO, chan]),
        ).crop(4, DURATION - 4) for chan in OSEMS[1::]
    },
    **{
        ':'.join([IFO, chan]): TimeSeries(
            numpy.random.normal(loc=1, scale=1.5, size=SCATTER.size),
            sample_rate=SAMPLE,
            name=':'.join([IFO, chan]),
        ).inject(SCATTER).crop(
            4, DURATION - 4) for chan in scattering_cli.TRANSMON_CHANNELS},
})

PHASE = PHASE[4 * SAMPLE:-4 * SAMPLE]
AUX['{}:SUS-ITMX_R0_DAMP_L_IN1_DQ'.format(IFO)] += 1.064 * PHASE / 2


# -- cli tests ----------------------------------------------------------------

@mock.patch(
    'gwpy.segments.DataQualityFlag.query',
    return_value=EMPTY_FLAG,
)
def test_main_no_livetime(flag, caplog, tmpdir):
    outdir = str(tmpdir)
    args = [  # command-line arguments
        '-i', IFO,
        '4', str(DURATION - 4),
        '--state-flag', '{}:DCH-TEST_FLAG:1'.format(IFO),
        '--multiplier-for-threshold', '1',
        '--output-dir', outdir,
        '--omega-scans', '5',
        '--verbose',
    ]
    # test command-line tool with no livetime
    scattering_cli.main(args)
    assert ("Segment length 25 shorter than padding length 60.0, skipping "
            "segment 0-25" in caplog.text)
    assert ("Downloaded 0 segments for H1:DCH-TEST_FLAG:1 [0.00s livetime]"
            in caplog.text)
    assert "No events found during active scattering segments" in caplog.text
    with open(os.path.join(outdir, "index.html"), 'r') as f:
        assert "No active analysis segments were found" in f.read()
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
