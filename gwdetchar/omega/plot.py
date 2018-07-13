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

"""Plotting routines for Omega scans
"""

from __future__ import division

import os.path
import warnings

from matplotlib import rcParams
from matplotlib.colors import LogNorm

from gwpy.plotter import (SpectrogramPlot,
                          TimeSeriesPlot, Plot)

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

rcParams.update({
    'axes.labelsize': 20,
    'figure.subplot.bottom': 0.17,
    'figure.subplot.left': 0.1,
    'figure.subplot.right': 0.9,
    'figure.subplot.top': 0.90,
    'axes.labelsize': 24,
    'axes.labelpad': 2,
    'grid.color': 'gray',
})


# -- Utilities ----------------------------------------------------------------

def omega_plot(series, gpstime, span, channel, colormap='viridis', clim=None,
               qscan=False, ylabel=None):
    """Plot any GWPy Series object with a time axis
    """
    plot = series.crop(gpstime-span, gpstime+span).plot(figsize=[6.25, 5])
    ax = plot.gca()
    # set time axis units
    ax.set_epoch(gpstime)
    ax.set_xscale('auto-gps')
    if span <= 1.:
        ax.set_xlabel('Time [milliseconds]')
    else:
        ax.set_xlabel('Time [seconds]')
    # set y-axis properties
    chan = channel.replace('_', '\_')
    if qscan:
        ax.set_yscale('log')
        ax.set_title('%s at %s with $Q=%.1f$' % (chan, gpstime, series.q),
                     fontsize=12)
        plot.add_colorbar(cmap=colormap, clim=clim,
                          label='Normalized energy')
    else:
        ax.set_yscale('linear')
        ax.set_title('%s at %s' % (chan, gpstime), fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True, axis='y', which='both')
    plot.tight_layout()
    return plot
