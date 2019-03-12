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
import sys
from getpass import getuser
try:
    from unittest import mock
except ImportError:  # python < 3
    import mock

import pytest

from matplotlib import use
use('Agg')  # nopep8

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
<script src="https://code.jquery.com/jquery-1.12.3.min.js" type="text/javascript"></script>
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
    plots='\n<a id="a_X1-TEST_FLAG_66" target="_blank" title="Known (small) '
          'and active (large) analysis segments for X1:TEST_FLAG" '
          'class="fancybox" href="plots/X1-TEST_FLAG-0-66.png" '
          'data-fancybox-group="images">\n<img id="img_X1-TEST_FLAG_66" '
          'alt="X1-TEST_FLAG-0-66.png" class="img-responsive" '
          'src="plots/X1-TEST_FLAG-0-66.png" />\n</a>')

FLAG_HTML_NO_SEGMENTS = FLAG_CONTENT.format(
    content='<p>No segments were found.</p>', plots='')

FLAG = DataQualityFlag(known=[(0, 66)], active=[(0, 66)], name='X1:TEST_FLAG')


# -- HTML unit tests ----------------------------------------------------------

def test_fancy_plot():
    # create a dummy FancyPlot instance
    test = html.FancyPlot('test.png')
    assert test.img is 'test.png'
    assert test.caption is 'test.png'

    # check that its properties are unchanged when the argument
    # to FancyPlot() is also a FancyPlot instance
    test = html.FancyPlot(test)
    assert test.img is 'test.png'
    assert test.caption is 'test.png'


def test_finalize_static_urls(tmpdir):
    static = os.path.join(str(tmpdir), 'static')
    css, js = html.finalize_static_urls(static, html.CSS_FILES, html.JS_FILES)
    assert css == [
        'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/'
            'bootstrap.min.css',  # nopep8
        'https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/'
            'jquery.fancybox.min.css',  # nopep8
        'static/bootstrap-ligo.min.css']
    assert js == [
        'https://code.jquery.com/jquery-1.12.3.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.13.0/'
            'moment.min.js',  # nopep8
        'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/'
            'jquery.fancybox.min.js',  # nopep8
        'static/bootstrap-ligo.min.js']
    shutil.rmtree(str(tmpdir), ignore_errors=True)


def test_new_bootstrap_page():
    page = html.new_bootstrap_page()
    assert parse_html(str(page)) == parse_html(NEW_BOOTSTRAP_PAGE)


def test_write_param():
    page = html.write_param('test', 'test')
    assert parse_html(str(page)) == parse_html(
        '<p>\n<strong>test: </strong>\ntest\n</p>')


@pytest.mark.parametrize('args, kwargs, result', [
    (('test.html', 'Test link'), {},
     '<a href="test.html" target="_blank">Test link</a>'),
    (('test.html', 'Test link'), {'class_': 'test-case'},
     '<a class="test-case" href="test.html" target="_blank">Test link</a>'),
])
def test_html_link(args, kwargs, result):
    h1 = parse_html(html.html_link(*args, **kwargs))
    h2 = parse_html(result)
    assert h1 == h2


def test_cis_link():
    h1 = parse_html(html.cis_link('X1:TEST-CHANNEL'))
    h2 = parse_html(
        '<a style="font-family: Monaco, &quot;Courier New&quot;, '
        'monospace; color: black;" href="https://cis.ligo.org/channel/byname/'
        'X1:TEST-CHANNEL" target="_blank" title="CIS entry for '
        'X1:TEST-CHANNEL">X1:TEST-CHANNEL</a>'
    )
    assert h1 == h2


def test_fancybox_img():
    img = html.FancyPlot('X1-TEST_AUX-test-4.png')
    out = html.fancybox_img(img)
    assert parse_html(out) == parse_html(
        '<a class="fancybox" href="X1-TEST_AUX-test-4.png" target="_blank" '
            'data-fancybox-group="images" id="a_X1-TEST_AUX_4" '
            'title="X1-TEST_AUX-test-4.png">\n'
        '<img class="img-responsive" alt="X1-TEST_AUX-test-4.png" '
            'src="X1-TEST_AUX-test-4.png" id="img_X1-TEST_AUX_4"/>\n'
        '</a>')


def test_scaffold_plots():
    h1 = parse_html(html.scaffold_plots([
        html.FancyPlot('X1-TEST_AUX-test-4.png'),
        html.FancyPlot('X1-TEST_AUX-test-16.png')], nperrow=2))
    h2 = parse_html(
        '<div class="row">\n'
        '<div class="col-sm-6">\n'
        '<a class="fancybox" href="X1-TEST_AUX-test-4.png" target="_blank" '
            'id="a_X1-TEST_AUX_4" data-fancybox-group="images" '
            'title="X1-TEST_AUX-test-4.png">\n'
        '<img class="img-responsive" alt="X1-TEST_AUX-test-4.png" '
            'id="img_X1-TEST_AUX_4" src="X1-TEST_AUX-test-4.png" />\n'
        '</a>\n'
        '</div>\n'
        '<div class="col-sm-6">\n'
        '<a class="fancybox" href="X1-TEST_AUX-test-16.png" target="_blank"'
            ' id="a_X1-TEST_AUX_16" data-fancybox-group="images" '
            'title="X1-TEST_AUX-test-16.png">\n'
        '<img class="img-responsive" alt="X1-TEST_AUX-test-16.png" '
            'id="img_X1-TEST_AUX_16" src="X1-TEST_AUX-test-16.png" />\n'
        '</a>\n'
        '</div>\n'
        '</div>')
    assert h1 == h2


def test_write_arguments():
    page = html.write_arguments([('test', 'test')], 0, 1, flag='X1:TEST')
    assert '<h2>Parameters</h2>' in page
    assert '<strong>Start time: </strong>\n0 (1980-01-06 00:00:00)' in page
    assert '<strong>End time: </strong>\n1 (1980-01-06 00:00:01)' in page
    assert '<strong>State flag: </strong>\nX1:TEST' in page
    assert '<strong>test: </strong>\ntest' in page
    assert '<strong>Command line: </strong>' in page


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


def test_write_footer():
    date = datetime.datetime.now()
    out = html.write_footer(date=date, class_=True)
    assert parse_html(str(out)) == parse_html(
        HTML_FOOTER.format(user=getuser(), date=date))


@mock.patch("{}.Path.is_dir".format(html.Path.__module__))
@mock.patch("subprocess.check_output", return_value="{\"key\": 0}")
@pytest.mark.parametrize("isdir, cmd", [
    pytest.param(
        False,
        "{} -m pip list installed --format json".format(sys.executable),
        id="pip",
    ),
    pytest.param(
        True,
        "conda list --prefix {} --json".format(sys.prefix),
        id="conda",
    ),
])
def test_package_list(check_output, is_dir, isdir, cmd):
    is_dir.return_value = isdir
    assert html.package_list() == {"key": 0}
    check_output.assert_called_with(cmd.split())


@mock.patch(
    "gwdetchar.io.html.package_list",
    return_value=[
        {"name": "gwpy", "version": "1.0.0"},
        {"name": "gwdetchar", "version": "1.2.3"},
    ],
)
def test_package_table(package_list):
    assert parse_html(
        html.package_table(class_="test", caption="Test"),
    ) == parse_html(
        "<h2>Environment</h2><table class=\"test\"><caption>Test</caption>"
        "<thead>"
        "<tr><th scope=\"col\">Name</th><th scope=\"col\">Version</th></tr>"
        "</thead><tbody>"
        "<tr><td>gwdetchar</td><td>1.2.3</td></tr>"
        "<tr><td>gwpy</td><td>1.0.0</td></tr>"
        "</tbody></table>",
    )
