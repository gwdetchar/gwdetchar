# coding=utf-8
# Copyright (C) Alex Urban (2018-2019)
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

"""Plotting routines for scattering checks
"""

from gwpy.plot import Plot

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Joshua Smith <joshua.smith@ligo.org>' \
              'Andrew Lundgren <andrew.lundgren>@ligo.org>'


# -- custom plotting tools ----------------------------------------------------

def _format_timeseries(ax, gps, fringe, multipliers=(1, 2, 4, 8),
                       linewidth=1, thresh=None):
    """Helper tool to format a `~gwpy.timeseries.TimeSeries` plot axis
    """
    t1 = fringe.t0.value
    t2 = (fringe.t0 + fringe.duration).value
    if thresh is not None:
        ax.plot([t1, t2], [thresh, thresh], 'k--')
    for m in sorted(multipliers, reverse=True):
        ax.plot(m * fringe, label=r'$f\times %d$' % m, linewidth=linewidth)
    # format time axis
    ax.set_xlim([t1, t2])
    ax.set_xscale('seconds', epoch=gps)
    ax.grid(True, axis='x', which='major')
    ax.legend(loc='upper right')


def _format_spectrogram(ax, qspecgram, colormap='viridis'):
    """Helper tool to format a `~gwpy.spectrogram.Spectrogram` plot axis
    """
    ax.imshow(qspecgram)
    ax.colorbar(cmap=colormap, norm='linear', clim=(0, 25),
                label='Normalized energy')
    # format frequency axis
    ax.set_yscale('linear')
    ax.set_ylabel('Frequency [Hz]')
    ax.grid(True, axis='y', which='both')


def spectral_comparison(gps, qspecgram, fringe, output, thresh=15,
                        multipliers=(1, 2, 4, 8), colormap='viridis',
                        figsize=[12, 8]):
    """Compare a high-resolution spectrogram with projected fringe frequencies

    Parameters
    ----------
    gps : `float`
        reference GPS time (in seconds) to serve as the origin

    qspecgram : `~gwpy.spectrogram.Spectrogram`
        an interpolated high-resolution spectrogram

    fringe : `~gwpy.timeseries.TimeSeries`
        projected fringe frequencies (in Hz)

    output : `str`
        name of the output file

    thresh : `float`, optional
        frequency threshold (Hz) for scattering fringes, default: 15

    multipliers : `tuple`, optional
        collection of fringe harmonic numbers to plot, can be given in
        any order, default: `(1, 2, 4, 8)`

    colormap : `str`, optional
        matplotlib colormap to use, default: viridis

    figsize : `tuple`, optional
        size (width x height) of the final figure, default: `(12, 8)`
    """
    plot = Plot(figsize=figsize)
    # format spectral plot
    ax1 = plot.add_subplot(211)
    ax1.set_title('{0} at {1:.2f} with $Q$ of {2:.1f}'.format(
        qspecgram.name, gps, qspecgram.q))
    _format_spectrogram(ax1, qspecgram, colormap=colormap)
    ax1.set_xlabel(None)
    # format fringe frequency plot
    ax2 = plot.add_subplot(212, sharex=ax1)
    ax2.set_title('{} scattering fringes'.format(fringe.name))
    _format_timeseries(ax2, gps, fringe, multipliers=multipliers,
                       thresh=thresh)
    # format timeseries axes
    ax2.set_ylim([-1, 60])
    ax2.set_ylabel('Projected Frequency [Hz]')
    # save plot and close
    plot.savefig(output, bbox_inches='tight')
    plot.close()


def spectral_overlay(gps, qspecgram, fringe, output,
                     multipliers=(1, 2, 4, 8), figsize=[12, 4]):
    """Overlay scattering fringe projections on top of a high-resolution
    spectrogram

    Parameters
    ----------
    gps : `float`
        reference GPS time (in seconds) to serve as the origin

    qspecgram : `~gwpy.spectrogram.Spectrogram`
        an interpolated high-resolution spectrogram

    fringe : `~gwpy.timeseries.TimeSeries`
        projected fringe frequencies (in Hz)

    output : `str`
        name of the output file

    multipliers : `tuple`, optional
        collection of fringe harmonic numbers to plot, can be given in
        any order, default: `(1, 2, 4, 8)`

    figsize : `tuple`, optional
        size (width x height) of the final figure, default: `(12, 4)`
    """
    plot = Plot(figsize=figsize)
    ax = plot.gca()
    # format spectrogram plot
    ax.set_title('Fringes: {0}, Spectrogram: {1}'.format(
        fringe.name, qspecgram.name))
    _format_spectrogram(ax, qspecgram, colormap='binary')
    # overlay fringe frequencies
    _format_timeseries(ax, gps, fringe, multipliers=multipliers,
                       linewidth=1.5)
    ax.set_ylim([qspecgram.f0.to('Hz').value,
                 qspecgram.frequencies.max().to('Hz').value])
    # save plot and close
    plot.savefig(output, bbox_inches='tight')
    plot.close()
