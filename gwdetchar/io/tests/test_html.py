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

import os
import shutil
import datetime
from getpass import getuser

import pytest

from matplotlib import use
use('Agg')  # nopep8

try:  # python 3.x
    from io import StringIO
except ImportError:  # python 2.7
    from cStringIO import StringIO

from gwpy.segments import (Segment, DataQualityFlag)

from .. import html
from ..._version import get_versions
from ...utils import parse_html

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

VERSION = get_versions()['version']
COMMIT = get_versions()['full-revisionid']

NEW_BOOTSTRAP_PAGE = """<!DOCTYPE HTML PUBLIC \'-//W3C//DTD HTML 4.01 Transitional//EN\'>
<html lang="en">
<head>
<meta content="width=device-width, initial-scale=1.0" name="viewport" />
<link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet" type="text/css" media="all" />
<script src="https://code.jquery.com/jquery-1.11.2.min.js" type="text/javascript"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js" type="text/javascript"></script>
</head>
<body>
</body>
</html>"""  # nopep8

HTML_FOOTER = """<footer class="footer">
<div class="container">
<div class="row">
<div class="col-md-12">
<p>These results were obtained using <a style="color:#000;" href="https://github.com/gwdetchar/gwdetchar/tree/%s" target="_blank">gwdetchar version %s</a> by {user} at {date}.</p>
</div>
</div>
</div>
</footer>""" % (COMMIT, VERSION)  # nopep8

FLAG_CONTENT = """<div class="panel panel-warning">
<div class="panel-heading">
<a class="panel-title" href="#flag0" data-toggle="collapse" data-parent="#accordion">X1:TEST_FLAG</a>
</div>
<div id="flag0" class="panel-collapse collapse">
<div class="panel-body">{plots}
{content}
</div>
</div>
</div>"""  # nopep8

FLAG_HTML = FLAG_CONTENT.format(content="""<pre># seg\tstart\tstop\tduration
0\t0\t66\t66.0
</pre>""", plots='')

FLAG_HTML_WITH_PLOTS = FLAG_CONTENT.format(
    content='<pre># seg\tstart\tstop\tduration\n0\t0\t66\t66.0\n</pre>',
    plots='\n<a href="plots/X1-TEST_FLAG-0-66.png" target="_blank">\n'
          '<img src="plots/X1-TEST_FLAG-0-66.png" style="width: 100%;" />\n'
          '</a>')

FLAG_HTML_NO_SEGMENTS = FLAG_CONTENT.format(
    content='<p>No segments were found.</p>', plots='')

FLAG = DataQualityFlag(known=[(0, 66)], active=[(0, 66)], name='X1:TEST_FLAG')


# -- HTML unit tests ----------------------------------------------------------

def test_new_bootstrap_page():
    page = html.new_bootstrap_page()
    assert parse_html(str(page)) == parse_html(NEW_BOOTSTRAP_PAGE)


def test_write_param():
    page = html.write_param('test', 'test')
    assert parse_html(str(page)) == parse_html(
        '<p>\n<strong>test: </strong>\ntest\n</p>'
    )


def test_write_footer():
    date = datetime.datetime.now()
    out = html.write_footer(date=date, class_=True)
    assert parse_html(str(out)) == parse_html(
        HTML_FOOTER.format(user=getuser(), date=date))


def test_write_flag_html():
    page = html.write_flag_html(FLAG)
    assert parse_html(str(page)) == parse_html(FLAG_HTML)

    page2 = html.write_flag_html(
        DataQualityFlag(known=[], active=[], name='X1:TEST_FLAG'))
    assert parse_html(str(page2)) == parse_html(FLAG_HTML_NO_SEGMENTS)


def test_write_flag_html_with_plots(tmpdir):
    tmpdir.mkdir('plots')
    os.chdir(str(tmpdir))
    page = html.write_flag_html(FLAG, span=Segment(0, 66), plotdir='plots')
    assert parse_html(str(page)) == parse_html(FLAG_HTML_WITH_PLOTS)
    shutil.rmtree(str(tmpdir), ignore_errors=True)
