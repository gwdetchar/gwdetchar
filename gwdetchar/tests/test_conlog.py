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

"""Tests for the `gwdetchar.conlog` command-line interface
"""

import os
import numpy
import pytest
import shutil

from unittest import mock

from gwpy.timeseries import (
    TimeSeries,
    TimeSeriesDict,
)

from .. import conlog

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

# -- test data

(START, END) = (10, 60)
PREVIEW = 10

START_SIGNAL = TimeSeries(
    numpy.sin(2 * numpy.pi * numpy.arange(PREVIEW + 1) / 7),
    sample_rate=1,
    epoch=START - PREVIEW,
)
END_SIGNAL = TimeSeries(
    numpy.sin(2 * numpy.pi * numpy.arange(END, END + 2) / 7),
    sample_rate=1,
    epoch=END,
)

START_DATA = TimeSeriesDict({
    "H1:AUX-CHANNEL_1.mean": START_SIGNAL,
    "H1:AUX-CHANNEL_2.mean": TimeSeries(
        numpy.ones(PREVIEW + 1),
        sample_rate=1,
        epoch=START - PREVIEW,
    ),
    "H1:AUX-CHANNEL_3.mean": TimeSeries(
        numpy.ones(PREVIEW + 1),
        sample_rate=1,
        epoch=START - PREVIEW,
    ),
    "H1:AUX-CHANNEL_4.mean": TimeSeries(
        numpy.ones(PREVIEW + 1),
        sample_rate=1,
        epoch=START - PREVIEW,
    ),
})

END_DATA = TimeSeriesDict({
    "H1:AUX-CHANNEL_1.mean": END_SIGNAL,
    "H1:AUX-CHANNEL_2.mean": TimeSeries(
        numpy.ones(2),
        sample_rate=1,
        epoch=END,
    ),
    "H1:AUX-CHANNEL_3.mean": TimeSeries(
        2 * numpy.ones(2),
        sample_rate=1,
        epoch=END,
    ),
    "H1:AUX-CHANNEL_4.mean": TimeSeries(
        -4 * numpy.ones(2),
        sample_rate=1,
        epoch=END,
    ),
})


# -- cli tests ----------------------------------------------------------------

@pytest.mark.parametrize('args', (
    [],
    ['--search', 'CHANNEL_3'],
    ['--channels'],
))
@mock.patch(
    'gwdetchar.conlog._discover_data',
    return_value=(START_DATA, END_DATA),
)
@mock.patch(
    'gwdetchar.conlog._discover_data_source',
    return_value=(['/path/to/data1.gwf'],
                  ['/path/to/data2.gwf']),
)
@mock.patch(
    'gwdetchar.conlog._get_available_channels',
    return_value=set(START_DATA.keys()),
)
def test_main(gwf, src, data, args, caplog, tmpdir):
    outdir = str(tmpdir)
    outfile = os.path.join(outdir, "changes.csv")
    # write channels file
    if '--channels' in args:
        channels = os.path.join(outdir, "channels.txt")
        with open(channels, 'w') as fobj:
            fobj.write("H1:AUX-CHANNEL_4.mean")
        args.append(channels)
    # determine command-line arguments
    args = [
        str(START),
        str(END),
        '-i', 'H1',
        '--preview', str(PREVIEW),
        '--output', outfile,
    ] + args
    # test command-line tool
    conlog.main(args)
    assert 'record a state change between {0} and {1}'.format(
        START, END) in caplog.text
    assert 'Output written to {}'.format(outfile) in caplog.text
    assert os.path.getsize(outfile)
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)


@mock.patch(
    'gwdatafind.find_urls',
    return_value=[],
)
def test_main_no_data(src):
    args = [
        str(START),
        str(END),
        '-i', 'L1',
    ]
    with pytest.raises(RuntimeError) as exc:
        conlog.main(args)
    assert str(exc.value) == 'Could not find data in the time range requested'


@mock.patch(
    'gwpy.timeseries.TimeSeriesDict.read',
    return_value=END_DATA,
)
@mock.patch(
    'gwdetchar.conlog._discover_data_source',
    return_value=(['/path/to/data1.gwf'],
                  ['/path/to/data2.gwf']),
)
@mock.patch(
    'gwpy.io.gwf.iter_channel_names',
    return_value=list(END_DATA.keys()),
)
def test_main_no_change(gwf, src, data, tmpdir):
    outdir = str(tmpdir)
    outfile = os.path.join(outdir, "changes.csv")
    # determine command-line arguments
    args = [
        str(START),
        str(END),
        '-i', 'H1',
        '--preview', '1',
        '--output', outfile,
    ]
    # test command-line tool
    conlog.main(args)
    with open(outfile, 'r') as fobj:
        table = fobj.read()
    assert table == 'channel,initial_value,final_value,difference\n'
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
