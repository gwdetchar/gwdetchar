# coding=utf-8
# Copyright (C) Alex Urban (2018-)
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

"""Plotting routines for omega scans
"""

from matplotlib import (cm, rcParams)

from gwpy.plot.colors import GW_OBSERVATORY_COLORS

from ..plot import texify

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

rcParams.update({
    'savefig.transparent': False,
})


# -- internal formatting tools ------------------------------------------------

def _format_time_axis(ax, gps, span):
    """Format the time axis of an omega scan plot

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
    ax.grid(True, axis='x', which='major')


def _format_frequency_axis(ax, yscale='log'):
    """Format the frequency axis of an omega scan plot

    Parameters
    ----------
    ax : `~matplotlib.axis.Axis`
        the `Axis` object to format
    """
    ax.grid(True, axis='y', which='both')
    ax.set_yscale(yscale)
    ax.set_ylabel('Frequency [Hz]')


def _format_color_axis(ax, colormap='viridis', clim=None, norm='linear'):
    """Format the color axis of an omega scan spectral plot

    Parameters
    ----------
    ax : `~matplotlib.axis.Axis`
        the `Axis` object to format

    colormap : `str`
        matplotlib colormap to use, default: viridis

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
    title = texify(channel)
    ax.set_title(title)
    # save plot and close
    plot.savefig(output)
    plot.close()


def spectral_plot(data, gps, span, channel, output, colormap='viridis',
                  clim=None, nx=1400, yscale='log', norm='linear',
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

    colormap : `str`
        matplotlib colormap to use, default: viridis

    clim : `tuple` or `None`
        limits of the color axis, default: autoscale with log scaling

    yscale : `str`
        scaling of the frequency axis, default: log

    norm : `str`
        scaling of the color axis, only used if `clim` is given,
        default: linear

    nx : `int`
        number of points along the time axis, default: 500

    figsize : `tuple`
        size (width x height) of the final figure, default: `(12, 6)`
    """
    from gwpy.spectrogram import Spectrogram
    # construct plot
    if isinstance(data, Spectrogram):
        # plot interpolated spectrogram
        Q = data.q
        data = data.crop(gps-span/2, gps+span/2)
        nslice = max(1, int(data.shape[0] / nx))
        plot = data[::nslice].pcolormesh(figsize=figsize)
    else:
        # plot eventgram
        Q = data.meta['q']
        plot = data.tile('time', 'frequency', 'duration', 'bandwidth',
                         color='energy', figsize=figsize, antialiased=True)
    # set axis properties
    ax = plot.gca()
    _format_time_axis(ax, gps=gps, span=span)
    _format_frequency_axis(ax, yscale=yscale)
    # set colorbar properties
    _format_color_axis(ax, colormap=colormap, clim=clim, norm=norm)
    # set title
    title = '{0} with $Q$ of {1:.1f}'.format(texify(channel), Q)
    ax.set_title(title)
    # save plot and close
    plot.savefig(output)
    plot.close()


def write_qscan_plots(gps, channel, series, fscale='log', colormap='viridis'):
    """Custom plot utility for a full omega scan

    Parameters
    ----------
    gps : `float`
        reference GPS time (in seconds) to serve as the origin

    channel : `OmegaChannel`
        channel corresponding to these data

    series : `tuple`
        a collection of `TimeSeries`, `Spectrogram`, and `QGram` objects

    fscale : `str`
        scaling of the frequency axis, default: log

    colormap : `str`, optional
        matplotlib colormap to use, default: viridis
    """
    # unpack series objects
    xoft, hpxoft, wxoft, qgram, rqgram, qspec, rqspec = series
    # range over plot types
    fnames = channel.plots
    for span, png1, png2, png3, png4, png5, png6, png7, png8, png9 in zip(
        channel.pranges, fnames['qscan_whitened'],
        fnames['qscan_autoscaled'], fnames['qscan_highpassed'],
        fnames['timeseries_raw'], fnames['timeseries_highpassed'],
        fnames['timeseries_whitened'], fnames['eventgram_highpassed'],
        fnames['eventgram_whitened'], fnames['eventgram_autoscaled']
    ):
        # plot whitened qscan
        spectral_plot(
            qspec, gps, span, channel.name, str(png1), clim=(0, 25),
            yscale=fscale, colormap=colormap)
        # plot autoscaled, whitened qscan
        spectral_plot(qspec, gps, span, channel.name, str(png2),
                      yscale=fscale, colormap=colormap)
        # plot raw qscan
        spectral_plot(
            rqspec, gps, span, channel.name, str(png3), clim=(0, 25),
            yscale=fscale, colormap=colormap)
        # plot raw timeseries
        timeseries_plot(xoft, gps, span, channel.name, str(png4),
                        ylabel='Amplitude')
        # plot highpassed timeseries
        timeseries_plot(hpxoft, gps, span, channel.name, str(png5),
                        ylabel='Highpassed Amplitude')
        # plot whitened timeseries
        timeseries_plot(wxoft, gps, span, channel.name, str(png6),
                        ylabel='Whitened Amplitude')
        # plot raw eventgram
        rtable = rqgram.table(snrthresh=channel.snrthresh)
        spectral_plot(
            rtable, gps, span, channel.name, str(png7), clim=(0, 25),
            yscale=fscale, colormap=colormap)
        # plot whitened eventgram
        table = qgram.table(snrthresh=channel.snrthresh)
        spectral_plot(
            table, gps, span, channel.name, str(png8), clim=(0, 25),
            yscale=fscale, colormap=colormap)
        # plot autoscaled whitened eventgram
        spectral_plot(table, gps, span, channel.name, str(png9),
                      yscale=fscale, colormap=colormap)
    return
