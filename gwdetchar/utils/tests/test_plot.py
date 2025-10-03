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

"""Tests for `gwdetchar.plot`
"""

import os
import shutil
import warnings

from unittest.mock import patch

from gwpy.segments import DataQualityFlag

from matplotlib import (
    use,
    rcParams,
    MatplotlibDeprecationWarning,
)
use('Agg')

# backend-dependent import
from .. import plot  # noqa: E402

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# -- test utilities -----------------------------------------------------------

def test_texify():
    name = 'X1:TEST-CHANNEL_NAME'

    # ignore deprecation warnings for rcParams
    warnings.simplefilter('ignore', MatplotlibDeprecationWarning)

    # test with LaTeX
    with patch.dict(rcParams, {'text.usetex': True}):
        assert plot.texify(name) == name.replace('_', r'\_')

    # test without LaTeX
    with patch.dict(rcParams, {'text.usetex': False}):
        assert plot.texify(name) == name

    # null use case
    assert plot.texify(None) == ''


# -- make sure plots run end-to-end -------------------------------------------

def test_plot_segments(tmpdir):
    base = str(tmpdir)
    flag = DataQualityFlag(
        known=[(0, 66)],
        active=[(16, 42)],
        name='X1:TEST-FLAG:1',
    )
    segplot = plot.plot_segments(flag, span=(0, 66))
    segplot.savefig(os.path.join(base, 'test.png'))
    shutil.rmtree(base, ignore_errors=True)
