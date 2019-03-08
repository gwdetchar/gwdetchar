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
import shutil
import tempfile
import atexit
import warnings

from matplotlib import rcParams

from gwpy.plot import Plot

from ..plot import get_gwpy_tex_settings

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Alex Macedo, Jeff Bidler, Oli Patane, Marissa Walker, ' \
              'Josh Smith'

# TeX settings
tex_settings = get_gwpy_tex_settings()
rcParams.update(tex_settings)


# -- plotting utilities -------------------------------------------------------

def configure_mpl():
    """Configure Matplotlib while processing channels with `gwdetchar.lasso`
    """
    import matplotlib
    matplotlib.use('agg')

    mpldir = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, mpldir)
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(mpldir, 0o777 & ~umask)
    os.environ['HOME'] = mpldir
    os.environ['MPLCONFIGDIR'] = mpldir

    class TexManager(matplotlib.texmanager.TexManager):
        texcache = os.path.join(mpldir, 'tex.cache')

    matplotlib.texmanager.TexManager = TexManager
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


def save_legend(axes, pngfile, loc='center', frameon=False, fontsize='small',
                **kwargs):
    """Save a figure with a legend
    """
    fig = Plot()
    leg = fig.legend(*axes.get_legend_handles_labels(), loc=loc,
                     frameon=frameon, fontsize=fontsize, **kwargs)
    for line in leg.get_lines():
        line.set_linewidth(8)
    fig.canvas.draw_idle()
    return save_figure(fig, pngfile,
                       bbox_inches=(leg.get_window_extent().transformed(
                           fig.dpi_scale_trans.inverted())))
