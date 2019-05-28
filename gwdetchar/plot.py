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

from gwpy.plot.tex import label_to_latex

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Dan Hoak <daniel.hoak@ligo.org>, ' \
              'Duncan Macleod <duncan.macleod@ligo.org>'


# -- plotting utilities -------------------------------------------------------

def texify(text):
    """Helper utility to detect when LaTeX rendering is used, and convert
    text to a LaTeX-passable representation if necessary

    Parameters
    ----------
    text : str
        text to convert to LaTeX representation

    Returns
    -------
    out : str
        either a copy or LaTeX representation of `text`

    See Also
    --------
    gwpy.plot.tex.label_to_latex
        the underlying method to convert to a LaTeX representation
    """
    if rcParams['text.usetex']:
        return label_to_latex(text)
    return text or ''


def plot_segments(flag, span, facecolor='red', edgecolor='darkred', height=0.8,
                  known={'alpha': 0.6, 'facecolor': 'lightgray',
                         'edgecolor': 'gray', 'height': 0.4}):
    """Plot the saturation segments contained within a flag
    """
    name = texify(flag.name)
    plot = flag.plot(
        figsize=[12, 2], facecolor=facecolor, edgecolor=edgecolor,
        height=height, known=known, label=' ', xlim=span, xscale='auto-gps',
        epoch=span[0], title="{} segments".format(name),
    )
    plot.subplots_adjust(bottom=0.4, top=0.8)
    return plot
