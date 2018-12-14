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


# -- internal formatting tools ------------------------------------------------

def _format_time_axis(ax, gps, span):
    """Format the time axis of an Omega scan plot

    Parameters
    ----------
    ax : `~matplotlib.axis.Axis`
        the `Axis` object to format

    gps : `float`
        reference GPS time (in seconds) to serve as the origin

    span : `float`
        total duration (in seconds) of the time axis
    """
    # set time axis units
    ax.set_xscale('seconds', epoch=gps)
    ax.set_xlim(gps-span/2, gps+span/2)
    ax.set_xlabel('Time [seconds]')
    ax.grid(True, axis='x', which='major')


def _format_frequency_axis(ax, axis='y'):
    """Format the frequency axis of an Omega scan plot

    Parameters
    ----------
    ax : `~matplotlib.axis.Axis`
        the `Axis` object to format

    axis : `str`
        a string identifiying the axis to format, must be either `'x'` or `'y'`
    """
    ax.grid(True, axis=axis, which='both')
    if axis == 'x':
        ax.set_xscale('log')
        ax.set_xlabel('Frequency [Hz]')
    else:
        ax.set_yscale('log')
        ax.set_ylabel('Frequency [Hz]')


def _format_color_axis(ax, colormap='viridis', clim=None, norm='linear'):
    """Format the color axis of an Omega scan spectral plot

    Parameters
    ----------
    ax : `~matplotlib.axis.Axis`
        the `Axis` object to format

    colormap : `str`
        Matplotlib colorbar to use, default: viridis

    clim : `tuple` or `None`
        limits of the color axis, default: autoscale with log scaling

    norm : `str`
        scaling of the color axis, only used if `clim` is given,
        default: linear
    """
    cmap = cm.get_cmap(colormap)
    ax.set_facecolor(cmap(0))
    # set colorbar format
    if clim is None:  # force a log colorbar with autoscaled limits
        ax.colorbar(cmap=colormap, norm='log', vmin=0.5,
                    label='Normalized energy')
    else:
        ax.colorbar(cmap=colormap, norm=norm, clim=clim,
                    label='Normalized energy')


# -- utilities ----------------------------------------------------------------

def timeseries_plot(data, gps, span, channel, output, ylabel=None,
                    figsize=(12, 6)):
    """Custom plot for a GWPy TimeSeries object

    Parameters
    ----------
    data : `~gwpy.timeseries.TimeSeries`
        the series to plot

    gps : `float`
        reference GPS time (in seconds) to serve as the origin

    span : `float`
        total duration (in seconds) of the time axis

    channel : `str`
        name of the channel corresponding to this data

    output : `str`
        name of the output file

    ylabel : `str` or `None`
        label for the y-axis

    figsize : `tuple`
        size (width x height) of the final figure, default: `(12, 6)`
    """
    # set color by IFO
    ifo = channel[:2]
    data = data.crop(gps-span/2, gps+span/2)
    plot = data.plot(color=GW_OBSERVATORY_COLORS[ifo], figsize=figsize)
    # set axis properties
    ax = plot.gca()
    _format_time_axis(ax, gps=gps, span=span)
    ax.set_yscale('linear')
    ax.set_ylabel(ylabel)
    # set title
    title = '%s at %.3f' % (channel, gps)
    ax.set_title(title, y=1.05)
    # save plot and close
    plot.savefig(output, bbox_inches='tight')
    plot.close()


def spectral_plot(data, gps, span, channel, output, ylabel=None,
                  colormap='viridis', clim=None, nx=500, norm='linear',
                  figsize=(12, 6)):
    """Custom plot for a GWPy spectrogram or Q-gram

    Parameters
    ----------
    data : `~gwpy.timeseries.TimeSeries`
        the series to plot

    gps : `float`
        reference GPS time (in seconds) to serve as the origin

    span : `float`
        total duration (in seconds) of the time axis

    channel : `str`
        name of the channel corresponding to this data

    output : `str`
        name of the output file

    ylabel : `str` or `None`
        label for the y-axis

    colormap : `str`
        Matplotlib colorbar to use, default: viridis

    clim : `tuple` or `None`
        limits of the color axis, default: autoscale with log scaling

    norm : `str`
        scaling of the color axis, only used if `clim` is given,
        default: linear

    nx : `int`
        number of points along the time axis, default: 500

    figsize : `tuple`
        size (width x height) of the final figure, default: `(12, 6)`
    """
    import numpy
    from gwpy.spectrogram import Spectrogram
    Q = data.q
    # construct plot
    if isinstance(data, Spectrogram):
        # plot interpolated spectrogram
        data = data.crop(gps-span/2, gps+span/2)
        nslice = max(1, int(data.shape[0] / nx))
        plot = data[::nslice].imshow(figsize=figsize)
    else:
        # plot eventgram
        cmap = cm.get_cmap(colormap)
        plot = data.tile('central_time', 'central_freq', 'duration',
                         'bandwidth', color='energy', figsize=figsize,
                         edgecolors=cmap(0), linewidth=0.1, antialiased=True)
    # set axis properties
    ax = plot.gca()
    _format_time_axis(ax, gps=gps, span=span)
    _format_frequency_axis(ax)
    # set colorbar properties
    _format_color_axis(ax, colormap=colormap, clim=clim, norm=norm)
    # set title
    title = '%s at %.3f with $Q$ of %.1f' % (channel, gps, Q)
    ax.set_title(title, y=1.05)
    # save plot and close
    plot.savefig(output, bbox_inches='tight')
    plot.close()


def omega_plot(data, gps, span, channel, output, ylabel=None,
               colormap='viridis', clim=None, nx=500, figsize=(12, 6)):
    """Plot any Omega scan data object

    Parameters
    ----------
    data : `~gwpy.timeseries.TimeSeries`
        the series to plot

    gps : `float`
        reference GPS time (in seconds) to serve as the origin

    span : `float`
        total duration (in seconds) of the time axis

    channel : `str`
        name of the channel corresponding to this data

    output : `str`
        name of the output file

    ylabel : `str` or `None`
        label for the y-axis

    colormap : `str`
        Matplotlib colorbar to use, default: viridis

    clim : `tuple` or `None`
        limits of the color axis, default: autoscale with log scaling

    nx : `int`
        number of points along the time axis, default: 500

    figsize : `tuple`
        size (width x height) of the final figure, default: `(12, 6)`
    """
    from gwpy.timeseries import TimeSeries
    if isinstance(data, TimeSeries):
        timeseries_plot(data, gps, span, channel, output, ylabel=ylabel,
                        figsize=figsize)
    else:
        spectral_plot(data, gps, span, channel, output, ylabel=ylabel,
                      colormap=colormap, clim=clim, nx=nx, figsize=figsize)
