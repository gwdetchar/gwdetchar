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

from matplotlib import (use, cm, rcParams)
use('agg')  # nopep8

from gwpy.plot.colors import GW_OBSERVATORY_COLORS

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

rcParams.update({
    'text.usetex': 'false',
    'font.family': 'sans-serif',
    'font.sans-serif': 'Arial',
    'figure.subplot.bottom': 0.17,
    'figure.subplot.left': 0.1,
    'figure.subplot.right': 0.9,
    'figure.subplot.top': 0.90,
    'axes.labelsize': 20,
    'axes.labelpad': 10,
    'axes.titlesize': 14,
    'grid.color': 'gray',
})


# -- Utilities ----------------------------------------------------------------

def omega_plot(series, gps, span, channel, output, colormap='viridis',
               clim=None, qscan=False, eventgram=False, ylabel=None,
               figsize=[12, 6]):
    """Plot any GWPy Series object with a time axis
    """
    # construct plot
    if qscan:
        # plot Q-transform
        plot = series.crop(gps-span/2, gps+span/2).imshow(figsize=figsize)
    elif eventgram:
        # plot eventgram
        plot = series.tile('central_time', 'central_freq', 'duration',
                           'bandwidth', color='energy', figsize=figsize)
    else:
        # set color by IFO
        ifo = channel[:2]
        series = series.crop(gps-span/2, gps+span/2)
        plot = series.plot(color=GW_OBSERVATORY_COLORS[ifo],
                           figsize=figsize)
    ax = plot.gca()
    # set time axis units
    ax.set_xscale('seconds', epoch=gps)
    ax.set_xlim(gps-span/2, gps+span/2)
    ax.set_xlabel('Time [seconds]')
    # set y-axis properties
    if (qscan or eventgram):
        ax.set_yscale('log')
        title = '%s at %.3f with $Q$ of %.1f' % (channel, gps, series.q)
        ax.colorbar(cmap=colormap, clim=clim, label='Normalized energy')
    else:
        ax.set_yscale('linear')
        title = '%s at %.3f' % (channel, gps)
    ax.set_title(title, y=1.05)
    if ylabel:
        ax.set_ylabel(ylabel)
    if eventgram:
        cmap = cm.get_cmap(colormap)
        rgba = cmap(0)
        ax.set_facecolor(rgba)
        ax.set_yscale('log')
        ax.set_ylabel('Frequency [Hz]')
    ax.grid(True, axis='y', which='both')
    # save plot and close
    plot.savefig(output, bbox_inches='tight')
    plot.close()
