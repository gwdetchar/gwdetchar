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

try:  # python 3.x
    from io import StringIO
    from html.parser import HTMLParser
    from html.entities import name2codepoint
except:  # python 2.7
    from cStringIO import StringIO
    from HTMLParser import HTMLParser
    from htmlentitydefs import name2codepoint

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

    def handle_comment(self, data):
        print("Comment:", data)

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        print("Named entity:", c)

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        print("Numeric entity:", c)

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


def natural_sort(l, key=str):
    """Sort a list the way that humans expect.

    This differs from the built-in `sorted` method by building a custom
    key to sort numeric parts by value, not by character content, so that
    '2' gets sorted before '10', for example.

    Parameters
    ----------
    l : `iterable`
        iterable to sort
    key : `callable`
        sorting key

    Returns
    -------
    sorted : `list`
        a sorted version of the input list
    """
    l = list(l)
    k = list(map(key, l)) if key else l
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in
                                re.split('([0-9]+)', k[l.index(key)])]
    return sorted(l, key=alphanum_key)
