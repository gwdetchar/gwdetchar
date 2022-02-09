# coding=utf-8
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
# along with GW DetChar.  If not, see <http://www.gnu.org/licenses/>.

"""Plotting utilities for gwdetchar.lasso
"""

import os
import re
import atexit
import shutil
import tempfile
import warnings

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Alex Macedo, Jeff Bidler, Oli Patane, Marissa Walker, ' \
              'Josh Smith'


# -- plotting utilities -------------------------------------------------------

def configure_mpl_tex():
    """Configure Matplotlib with LaTeX when using multiprocessing
    """
    import matplotlib
    matplotlib.use('agg')

    from matplotlib import texmanager

    mpldir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, mpldir)
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(mpldir, 0o777 & ~umask)
    os.environ['HOME'] = mpldir
    os.environ['MPLCONFIGDIR'] = mpldir

    class TexManager(texmanager.TexManager):
        texcache = os.path.join(mpldir, 'tex.cache')

    texmanager.TexManager = TexManager
    matplotlib.rcParams['ps.useafm'] = True
    matplotlib.rcParams['pdf.use14corefonts'] = True
    matplotlib.rcParams['text.usetex'] = True


def save_figure(fig, pngfile, **kwargs):
    """Save a figure
    """
    try:
        fig.save(pngfile, **kwargs)
    except (RuntimeError, IOError, IndexError):
        try:
            fig.save(pngfile, **kwargs)
        except (RuntimeError, IOError, IndexError) as e:
            warnings.warn('Error saving {0}: {1}'.format(pngfile, str(e)))
            return
    fig.close()
    return pngfile


def make_spectrum_plot(unfiltered_spectrum, filtered_spectrum, channel_name,
                       x_min, x_max, y_min, y_max, x_label, y_label, title,
                       filename):
    """Generate and return a spectrum plot
    """
    fig = unfiltered_spectrum.plot(label='Unfiltered', color='#ee0000')
    ax = fig.gca()
    ax.plot(filtered_spectrum, label='Filtered', color='#92ddc8')
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel('Frequency [Hz]', fontsize='small')
    ax.set_ylabel(y_label, fontsize='small')
    ax.set_title(title, fontsize='small')
    ax.legend(loc='best', fontsize='small')
    spectrum_plot = save_figure(
        fig, filename, bbox_inches='tight')
    fig.close()
    return spectrum_plot


def make_spectrum_plots(start, end, flower, fupper, channel_name,
                        unfiltered_spectrum, filtered_spectrum):
    """Generate and return both spectrum plots
    """
    re_delim = re.compile(r'[:_-]')

    # Attributes shared between zoomed out and zoomed in plots
    channelstub = re_delim.sub('_', str(channel_name)).replace('_', '-', 1)
    gpsstub = '%d-%d' % (start, end-start)
    x_label = 'Frequency [Hz]'
    if ':GDS-CALIB_STRAIN' in channel_name:
        y_label = ('GW amplitude spectral density '
                   '[strain/$\\sqrt{\\mathrm{Hz}}]$')
    else:
        y_label = 'Primary channel units'
    y_min = 0.1 * filtered_spectrum.min().value
    y_max = 5 * filtered_spectrum.max().value

    # Atttributes specific to one of the two spectrum plots
    zoomed_out_x_min = 10
    zoomed_out_x_max = 2000
    zoomed_out_title = '%s band-passed spectrum (zoomed out)' % channelstub
    zoomed_out_spectrum_plot_name = ('%s-_BAND_PASSED_SPECTRUM_ZOOM_OUT-%s.png'
                                     % (channelstub, gpsstub))

    zoomed_in_x_min = flower - ((fupper - flower) * 0.1)
    zoomed_in_x_max = fupper + ((fupper - flower) * 0.1)
    zoomed_in_title = '%s band-passed spectrum (zoomed in)' % channelstub
    zoomed_in_spectrum_plot_name = ('%s-_BAND_PASSED_SPECTRUM_ZOOM_IN-%s.png'
                                    % (channelstub, gpsstub))

    # Generate both spectrum plots
    spectrum_plot_zoomed_out = make_spectrum_plot(
        unfiltered_spectrum, filtered_spectrum, channel_name,
        zoomed_out_x_min, zoomed_out_x_max, y_min, y_max, x_label, y_label,
        zoomed_out_title, zoomed_out_spectrum_plot_name)

    spectrum_plot_zoomed_in = make_spectrum_plot(
        unfiltered_spectrum, filtered_spectrum, channel_name,
        zoomed_in_x_min, zoomed_in_x_max, y_min, y_max, x_label, y_label,
        zoomed_in_title, zoomed_in_spectrum_plot_name)

    return (spectrum_plot_zoomed_out, spectrum_plot_zoomed_in)
