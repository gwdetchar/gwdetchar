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

"""Utility methods
"""

import re
import sys
from io import StringIO
from functools import partial
from html.parser import HTMLParser

import numpy

from gwpy.table import EventTable

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'


# -- class for HTML parsing ---------------------------------------------------

class GWHTMLParser(HTMLParser):
    """See https://docs.python.org/3/library/html.parser.html.
    """
    def handle_starttag(self, tag, attrs):
        print("Start tag:", tag)
        attrs.sort()
        for attr in attrs:
            print("attr:", attr)

    def handle_endtag(self, tag):
        print("End tag:", tag)

    def handle_data(self, data):
        print("Data:", data)

    def handle_decl(self, data):
        print("Decl:", data)


parser = GWHTMLParser()


# -- utilities ----------------------------------------------------------------

def parse_html(html):
    """Parse a string containing raw HTML code
    """
    stdout = sys.stdout
    sys.stdout = StringIO()
    if sys.version_info.major < 3:
        parser.feed(html.decode('utf-8', 'ignore'))
    else:
        parser.feed(html)
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    return output


def natural_sort(ls, key=str):
    """Sort a list the way that humans expect.

    This differs from the built-in `sorted` method by building a custom
    key to sort numeric parts by value, not by character content, so that
    '2' gets sorted before '10', for example.

    Parameters
    ----------
    ls : `iterable`
        iterable to sort
    key : `callable`
        sorting key

    Returns
    -------
    sorted : `list`
        a sorted version of the input list
    """
    ls = list(ls)
    k = list(map(key, ls)) if key else ls

    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum_key(key):
        return [convert(c) for c in
                re.split('([0-9]+)', k[ls.index(key)])]

    return sorted(ls, key=alphanum_key)


def table_from_segments(flagdict, sngl_burst=False, snr=10., frequency=100.):
    """Build an `EventTable` from a `DataQualityDict`
    """
    rows = []
    if sngl_burst:
        names = ("peak", "peak_frequency", "snr", "channel")

        def row(seg, channel):
            a, b = map(float, seg)
            return a, frequency, snr, channel
    else:
        names = ("time", "frequency", "start_time", "end_time",
                 "snr", "channel")

        def row(seg, channel):
            a, b = map(float, seg)
            return a, frequency, a, b, snr, channel

    for name, flag in flagdict.items():
        rows.extend(map(partial(row, channel=name), flag.active))
    table = EventTable(rows=rows or None, names=names)
    if sngl_burst:  # add tablename for GWpy's ligolw writer
        table.meta["tablename"] = "sngl_burst"
    return table


def table_from_times(times, names=("time", "frequency", "snr"),
                     snr=10., frequency=100., **kwargs):
    """Build an `EventTable` from a `DataQualityDict`

    Parameters
    ----------
    times : `numpy.ndarray`
        a 1D array of GPS times

    names : `tuple`, `list`, optional
        the list of names to use

    snr : `float`, optional
        the SNR to assign to all 'event triggers'

    frequency : `float`, optional
        the frequency to assign to all 'event triggers'

    **kwargs
        other keyword arguments to pass to the `EventTable` constructor

    Returns
    -------
    table : `~gwpy.table.EventTable`
        a new table filled with events at the given times
    """
    farr = numpy.ones_like(times) * frequency
    sarr = numpy.ones_like(times) * snr
    return EventTable([times, farr, sarr], names=names, **kwargs)
