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

from gwpy.segments import DataQualityFlag

from matplotlib import use
use('agg')

from .. import plot

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

FLAG = DataQualityFlag(known=[(0, 66)], active=[(16, 42)],
                       name='X1:TEST-FLAG:1')


# -- make sure plots run end-to-end -------------------------------------------

def test_plot_segments(tmpdir):
    base = str(tmpdir)
    segplot = plot.plot_segments(FLAG, span=(0, 66))
    segplot.savefig(os.path.join(base, 'test.png'))
    shutil.rmtree(base, ignore_errors=True) 
