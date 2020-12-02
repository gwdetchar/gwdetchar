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
import glob
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

# The unit test below captures use cases by simulating
#     (1) empty livetime from requested segments, and
#     (2) a scattering fringe in h(t) predicted by only one optic.

DURATION = 608
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
    assert "Downloaded 0 segments for H1:DCH-TEST_FLAG:1" in caplog.text
    assert "No events found during active scattering segments" in caplog.text
    assert not os.path.exists(os.path.join(outdir, 'scans'))
    with open(os.path.join(outdir, "index.html"), 'r') as f:
        assert "No active analysis segments were found" in f.read()
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)


@mock.patch(
    'gwtrigfind.find_trigger_files',
    return_value=[],
)
@mock.patch(
    'gwdetchar.scattering.__main__.get_data',
    return_value=AUX,
)
def test_main(cache, data, caplog, tmpdir, recwarn):
    outdir = str(tmpdir)
    args = [  # command-line arguments
        '-i', IFO,
        '4', str(DURATION - 4),
        '--multiplier-for-threshold', '1',
        '--output-dir', outdir,
        '--verbose',
    ]
    # test command-line tool
    scattering_cli.main(args)
    hdf = "{0}-SCATTERING_SEGMENTS_15_HZ-4-{1}.h5".format(IFO, DURATION - 8)
    assert "Processing %.2f s of livetime" % (DURATION - 8) in caplog.text
    assert "Searching for scatter based on OSEM velocity" in caplog.text
    assert ("Searching for scatter based on band-limited RMS of transmons"
            in caplog.text)
    assert "Writing a summary CSV record" in caplog.text
    assert ("The following 0 triggers fell within active scattering segments:"
            in caplog.text)
    assert "{0} written".format(hdf) in caplog.text
    assert "-- index.html written, all done --" in caplog.text
    for channel in AUX.keys():
        assert "-- Processing {0} --".format(channel) in caplog.text
        assert "Completed channel {0}".format(channel) in caplog.text
    # test output data products
    assert glob.glob(os.path.join(outdir, '*.png'))
    assert len(glob.glob(os.path.join(outdir, '*.csv'))) == 1
    assert len(glob.glob(os.path.join(outdir, '*.html'))) == 1
    assert os.path.exists(os.path.join(outdir, hdf))
    assert not os.path.exists(os.path.join(outdir, 'scans'))
    # reject warnings due to no Omicron triggers
    recwarn.pop(RuntimeWarning)
    recwarn.pop(UserWarning)
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
