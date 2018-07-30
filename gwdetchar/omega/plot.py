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

from matplotlib import cm
from matplotlib import rcParams
from matplotlib.colors import LogNorm

from gwpy.plotter import (SpectrogramPlot,
                          TimeSeriesPlot, Plot)
from gwpy.plotter.colors import GW_OBSERVATORY_COLORS

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

def omega_plot(series, gps, span, channel, colormap='viridis', clim=None,
               qscan=False, eventgram=False, ylabel=None, figsize=[12, 6]):
    """Plot any GWPy Series object with a time axis
    """
    # construct plot
    if qscan:
        # plot Q-transform
        plot = series.crop(gps-span/2, gps+span/2).plot(figsize=figsize)
    elif eventgram:
        # plot eventgram
        plot = series.plot('central_time', 'central_freq', 'duration',
                           'bandwidth', color='energy',
                           figsize=figsize)
    else:
        # set color by IFO
        ifo = channel[:2]
        series = series.crop(gps-span/2, gps+span/2)
        plot = series.plot(color=GW_OBSERVATORY_COLORS[ifo],
                           figsize=figsize)
    ax = plot.gca()
    # set time axis units
    ax.set_epoch(gps)
    ax.set_xscale('auto-gps')
    if span <= 1.:
        ax.set_xlabel('Time [milliseconds]')
    else:
        ax.set_xlabel('Time [seconds]')
    # set y-axis properties
    chan = channel.replace('_', '\_')
    if (qscan or eventgram):
        ax.set_yscale('log')
        ax.set_title('%s at %.3f with $Q=%.1f$' % (chan, gps, series.q),
                     fontsize=12)
        plot.add_colorbar(cmap=colormap, clim=clim,
                          label='Normalized energy')
    else:
        ax.set_yscale('linear')
        ax.set_title('%s at %.3f' % (chan, gps), fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel)
    if eventgram:
        cmap = cm.get_cmap(colormap)
        rgba = cmap(0)
        ax.set_facecolor(rgba)
        ax.set_xlim(gps-span/2, gps+span/2)
        ax.set_yscale('log')
        ax.set_ylabel('Frequency [Hz]')
    ax.grid(True, axis='y', which='both')
    plot.tight_layout()
    return plot
