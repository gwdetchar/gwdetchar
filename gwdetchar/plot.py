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

"""Plotting utilities
"""

from matplotlib import rcParams
from gwpy.plot.tex import (has_tex, MACROS as GWPY_TEX_MACROS)

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Dan Hoak <daniel.hoak@ligo.org>, ' \
              'Duncan Macleod <duncan.macleod@ligo.org>'


def get_gwpy_tex_settings():
    """Return a dict of rcParams similar to GWPY_TEX_RCPARAMS

    Returns
    -------
    rcParams : `dict`
        a dictionary of matplotlib rcParams
    """
    # custom GW-DetChar formatting
    params = {
        'font.size': 10,
        'xtick.labelsize': 18,
        'ytick.labelsize': 18,
        'axes.labelsize': 20,
        'axes.titlesize': 24,
        'grid.alpha': 0.5,
    }
    if has_tex():
        params.update({
            'text.usetex': True,
            'text.latex.preamble': (
                rcParams.get('text.latex.preamble', []) + GWPY_TEX_MACROS),
            'font.family': ['serif'],
            'axes.formatter.use_mathtext': False,
        })
    return params


# TeX settings
tex_settings = get_gwpy_tex_settings()
rcParams.update(tex_settings)


# -- plotting utilities -------------------------------------------------------

def plot_segments(flag, span, facecolor='red', edgecolor='darkred',
                  known={'alpha': 0.2, 'facecolor': 'lightgray',
                         'edgecolor': 'gray'}):
    """Plot the saturation segments contained within a flag
    """
    name = flag.texname if has_tex() else flag.name
    plot = flag.plot(
        figsize=[12, 2], facecolor=facecolor, edgecolor=edgecolor,
        known=known, label=' ',
        xlim=span, xscale='auto-gps', epoch=span[0],
        title="{} segments".format(name),
    )
    plot.subplots_adjust(bottom=0.4, top=0.8)
    return plot
