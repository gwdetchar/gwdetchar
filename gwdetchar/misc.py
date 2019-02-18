# coding=utf-8
# Copyright (C) Duncan Macleod (2015)
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
# along with GW DetChar.  If not, see <http://www.gnu.org/licenses/>.

"""Miscellaneous methods and utilities
"""

import numpy

from matplotlib import rcParams
from gwpy.plot.tex import MACROS as GWPY_TEX_MACROS

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def find_timeseries_value_changes(timeseries):
    """Find the times of changes in the value of a `TimeSeries`

    Parameters
    ----------
    timeseries : `~gwpy.timeseries.TimeSeries`
        the input data series

    Returns
    -------
    times : `numpy.ndarray`
        an array of GPS times (`~numpy.float64`) at which the given
        timeseries changed value
    """
    diff = numpy.diff(timeseries.value)
    times = timeseries.times.value[1:]
    return times[diff > 0]


def get_gwpy_tex_settings():
    """Return a dict of rcParams similar to GWPY_TEX_RCPARAMS

    Returns
    -------
    rcParams : `dict`
        a dictionary of matplotlib rcParams
    """
    return {
        # reproduce GWPY_TEX_PARAMS
        'text.usetex': True,
        'text.latex.preamble': (
            rcParams.get('text.latex.preamble', []) + GWPY_TEX_MACROS),
        'font.family': ['serif'],
        'axes.formatter.use_mathtext': False,
        # custom GW-DetChar formatting
        'font.size': 10,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'axes.labelsize': 20,
        'axes.titlesize': 24,
        'grid.alpha': 0.5,
    }
