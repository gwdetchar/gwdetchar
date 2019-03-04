# -*- coding: utf-8 -*-
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
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for `gwdetchar.io.html`
"""

import pytest

try:  # python 3.x
    from io import StringIO
except ImportError:  # python 2.7
    from cStringIO import StringIO

from gwpy.segments import DataQualityFlag

from .. import html
from ...utils import parse_html

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

NEW_BOOTSTRAP_PAGE = """<!DOCTYPE HTML PUBLIC \'-//W3C//DTD HTML 4.01 Transitional//EN\'>
<html lang="en">
<head>
<link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet" type="text/css" media="all" />
<script src="https://code.jquery.com/jquery-1.11.2.min.js" type="text/javascript"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js" type="text/javascript"></script>
</head>
<body>
</body>
</html>"""  # nopep8

FLAG_HTML = """<div class="panel panel-warning">
<div class="panel-heading">
<a class="panel-title" href="#flag0" data-toggle="collapse" data-parent="#accordion">
</div>
<div id="flag0" class="panel-collapse collapse">
<div class="panel-body">
<pre># seg\tstart\tstop\tduration
0\t0\t66\t66.0
</pre>
</div>
</div>
</div>"""  # nopep8

FLAG = DataQualityFlag(known=[(0, 66)], active=[(0, 66)])


# -- HTML unit tests ----------------------------------------------------------

def test_new_bootstrap_page():
    page = html.new_bootstrap_page()
    assert parse_html(str(page)) == parse_html(NEW_BOOTSTRAP_PAGE)


def test_write_param():
    page = html.write_param('test', 'test')
    assert parse_html(str(page)) == parse_html(
        '<p>\n<strong>test: </strong>\ntest\n</p>'
    )


def test_write_flag_html():
    page = html.write_flag_html(FLAG)
    assert parse_html(str(page)) == parse_html(FLAG_HTML)
