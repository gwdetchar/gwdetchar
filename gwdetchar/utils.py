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

from functools import partial
from html.parser import HTMLParser
from io import StringIO
import numpy
import operator
import re
import sys

from gwpy.segments import (DataQualityDict,
                           DataQualityFlag,
                           Segment,
                           SegmentList,
                           )
from gwpy.table import EventTable

re_flagdiv = re.compile(r"(&|!=|!|\|)")
re_cchar = re.compile(r"[\W_]+")

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = ('Alex Urban <alexander.urban@ligo.org>',
               'Evan Goetz <evan.goetz@ligo.org>',
               )


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


def split_compound_flag(compound):
    """Parse the configuration for this state.

    Returns
    -------
    flags : `tuple`
        a 2-tuple containing lists of flags defining required ON
        and OFF segments respectively for this state
    """
    # find flags
    divs = re_flagdiv.findall(compound)
    keys = re_flagdiv.split(compound)
    # load flags and vetoes
    union = []
    intersection = []
    exclude = []
    notequal = []
    for i, key in enumerate(keys[::2]):
        if not key:
            continue
        # get veto bit
        if i != 0 and divs[i-1] == '!':
            exclude.append(key)
        elif i != 0 and divs[i-1] == '|':
            union.append(key)
        elif i != 0 and divs[i-1] == '!=':
            notequal.append(key)
        else:
            intersection.append(key)
    return union, intersection, exclude, notequal


def get_states(states, names, gps_start_time, gps_end_time):
    """ Get states and return a DataQualityDict """
    flags = states.split(',')
    names = names.split(',')
    if 'all' in flags or 'All' in flags or 'ALL' in flags:
        allstate = True
        if 'all' in flags:
            names.remove(names[flags.index('all')])
            flags.remove('all')
        elif 'All' in flags:
            names.remove(names[flags.index('All')])
            flags.remove('All')
        else:
            names.remove(names[flags.index('ALL')])
            flags.remove('ALL')
    allflags = set([f for cf in flags for f in
                    re_flagdiv.split(str(cf))[::2] if f])

    for idx, name in enumerate(names):
        names[idx] = re_cchar.sub('_', name.lower())

    start = gps_start_time
    end = gps_end_time
    span = SegmentList([Segment(start, end)])

    dqdict = DataQualityDict()
    for f, n in zip(flags, names):
        dqdict[f] = DataQualityFlag(f, known=span, active=span,
                                    description=n)
    dqdict_all = DataQualityDict.query_dqsegdb(allflags, span)

    for compound in flags:
        union, intersection, exclude, notequal = split_compound_flag(
            compound)
        if len(f := (union + intersection)) == 1:
            dqdict[compound].description = dqdict_all[f[0]].description
            dqdict[compound].padding = (0, 0)
        for flist, op in zip([exclude, intersection, union, notequal],
                             [operator.sub, operator.and_, operator.or_,
                              notequal]):
            for f in flist:
                segs = dqdict_all[f].copy()
                segs = segs.coalesce()  # just in case
                dqdict[compound] = op(dqdict[compound], segs)
            dqdict[compound].known &= span
            dqdict[compound].active &= span
            dqdict[compound].coalesce()

    if allstate:
        dqdict['all'] = DataQualityFlag('all', known=span, active=span,
                                        description='all')

    return dqdict
