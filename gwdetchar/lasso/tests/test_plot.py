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

import numpy
import os
import pytest
import shutil

from gwpy.timeseries import TimeSeries

from matplotlib import (
    use,
    rcParams,
    rcParamsDefault,
)
use('Agg')

# backend-dependent import
from .. import plot  # noqa: E402

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# -- make sure plots run end-to-end -------------------------------------------

def test_configure_mpl_tex():
    plot.configure_mpl_tex()
    assert os.environ['HOME'] == os.environ['MPLCONFIGDIR']
    assert rcParams['ps.useafm'] is True
    assert rcParams['pdf.use14corefonts'] is True
    assert rcParams['text.usetex'] is True
    rcParams.update(rcParamsDefault)


def test_save_figure(tmpdir):
    base = str(tmpdir)
    series = TimeSeries(numpy.random.normal(loc=0, scale=1, size=24*60),
                        sample_rate=60, unit='Mpc', name='X1:TEST')
    fig = series.plot()
    tsplot = plot.save_figure(fig, os.path.join(base, 'test.png'))
    assert tsplot == os.path.join(base, 'test.png')

    # no-directory should raise warning
    with pytest.warns(UserWarning) as record:
        noneplot = plot.save_figure(fig, os.path.join('tgpflk', 'test.png'))
    assert noneplot is None
    assert len(record.list) == 1
    assert 'Error saving' in str(record.list[0].message)

    # remove base directory
    shutil.rmtree(base, ignore_errors=True)
