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
import sys
import shutil
import datetime
import sys
from pytz import reference
from getpass import getuser
from MarkupPy import markup
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

NEW_BOOTSTRAP_PAGE = """<!DOCTYPE HTML>
<html lang="en">
<head>
<meta http-equiv="refresh" content="60" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta content="width=device-width, initial-scale=1.0" name="viewport" />
<base href="{base}" />
<link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet" type="text/css" media="all" />
<link href="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css" rel="stylesheet" type="text/css" media="all" />
<link href="static/bootstrap-ligo.min.css" rel="stylesheet" type="text/css" media="all" />
<link href="static/gwdetchar.min.css" rel="stylesheet" type="text/css" media="all" />
<script src="https://code.jquery.com/jquery-1.12.3.min.js" type="text/javascript"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.13.0/moment.min.js" type="text/javascript"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js" type="text/javascript"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.js" type="text/javascript"></script>
<script src="static/bootstrap-ligo.min.js" type="text/javascript"></script>
<script src="static/gwdetchar.min.js" type="text/javascript"></script>
</head>
<body>
<div class="container">
</body>
</html>"""  # nopep8

TEST_CONFIGURATION = """[section]
key = value"""

ABOUT = """<div class="row">
<div class="col-md-12">
<h2>On the command-line</h2>
<p>This page was generated with the following command-line call:</p>
<div class="highlight" style="background: #f8f8f8"><pre style="line-height: 125%"><span></span>$ gwdetchar-scattering -i X1
</pre></div>

<p>The install path used was <code>{}</code>.</p>
<h2>Configuration files</h2>
<p>The following INI-format configuration file(s) were passed on the comand-line and are reproduced here in full:</p>
<div class="highlight" style="background: #f8f8f8"><pre style="line-height: 125%"><span></span><span style="color: #008000; font-weight: bold">[section]</span>
<span style="color: #7D9029">key</span> <span style="color: #666666">=</span> <span style="color: #BA2121">value</span>
</pre></div>

<h2>Environment</h2><table class="table table-hover table-condensed table-responsive" id="package-table"><caption>Table of packages installed in the production environment</caption><thead><tr><th scope="col">Name</th><th scope="col">Version</th></tr></thead><tbody><tr><td>gwdetchar</td><td>1.2.3</td></tr><tr><td>gwpy</td><td>1.0.0</td></tr></tbody></table><button class="btn btn-default btn-table" onclick="exportTableToCSV(&quot;package-table.csv&quot;, &quot;package-table&quot;)">Export to CSV</button>
</div>
</div>""".format(sys.prefix)  # nopep8

ABOUT_WITH_CONFIG_LIST = """<div class="row">
<div class="col-md-12">
<h2>On the command-line</h2>
<p>This page was generated with the following command-line call:</p>
<div class="highlight" style="background: #f8f8f8"><pre style="line-height: 125%"><span></span>$ gwdetchar-scattering -i X1
</pre></div>

<p>The install path used was <code>{}</code>.</p>
<h2>Configuration files</h2>
<p>The following INI-format configuration file(s) were passed on the comand-line and are reproduced here in full:</p>
<div class="panel-group" id="accordion">
<div class="panel panel-default">
<a href="#file0" data-toggle="collapse" data-parent="#accordion">
<div class="panel-heading">
<h4 class="panel-title">test.ini</h4>
</div>
</a>
<div id="file0" class="panel-collapse collapse">
<div class="panel-body">
<div class="highlight" style="background: #f8f8f8"><pre style="line-height: 125%"><span></span><span style="color: #008000; font-weight: bold">[section]</span>
<span style="color: #7D9029">key</span> <span style="color: #666666">=</span> <span style="color: #BA2121">value</span>
</pre></div>

</div>
</div>
</div>
</div>
<h2>Environment</h2><table class="table table-hover table-condensed table-responsive" id="package-table"><caption>Table of packages installed in the production environment</caption><thead><tr><th scope="col">Name</th><th scope="col">Version</th></tr></thead><tbody><tr><td>gwdetchar</td><td>1.2.3</td></tr><tr><td>gwpy</td><td>1.0.0</td></tr></tbody></table><button class="btn btn-default btn-table" onclick="exportTableToCSV(&quot;package-table.csv&quot;, &quot;package-table&quot;)">Export to CSV</button>
</div>
</div>""".format(sys.prefix)  # nopep8

HTML_FOOTER = """<footer class="footer">
<div class="container">
<div class="row">
<div class="col-md-12">
<p>This page was created by {user} at {date}.</p>
<p><a href="https://github.com/gwdetchar/gwdetchar/tree/%s" target="_blank">View gwdetchar-%s on GitHub</a> | <a href="https://github.com/gwdetchar/gwdetchar/issues" target="_blank">Report an issue</a></p>
</div>
</div>
</div>
</footer>""" % (COMMIT, VERSION)  # nopep8

HTML_CLOSE = """</div>
%s
</body>
</html>""" % HTML_FOOTER  # nopep8

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

OMEGA_SCAFFOLD = """<div class="panel well panel-default">
<div class="panel-heading clearfix">
<h3 class="panel-title"><a href="https://cis.ligo.org/channel/byname/X1:STRAIN" title="CIS entry for X1:STRAIN" style="font-family: Monaco, &quot;Courier New&quot;, monospace; color: black;" target="_blank">X1:STRAIN</a></h3>
</div>
<ul class="list-group">
<li class="list-group-item">
<div class="container">
<div class="row">
<div class="pull-right">
<a href="./1126259462" class="text-dark">[full scan]</a>
</div>
<h4>1126259462</h4>
</div>
<div class="row">
<div class="col-sm-4">
<a href="./1126259462/plots/X1-STRAIN-qscan_whitened-1.png" id="a_X1-STRAIN_1" title="X1-STRAIN-qscan_whitened-1.png" class="fancybox" target="_blank" data-fancybox-group="images">
<img id="img_X1-STRAIN_1" alt="X1-STRAIN-qscan_whitened-1.png" class="img-responsive" src="./1126259462/plots/X1-STRAIN-qscan_whitened-1.png" />
</a>
</div>
<div class="col-sm-4">
<a href="./1126259462/plots/X1-STRAIN-qscan_whitened-4.png" id="a_X1-STRAIN_4" title="X1-STRAIN-qscan_whitened-4.png" class="fancybox" target="_blank" data-fancybox-group="images">
<img id="img_X1-STRAIN_4" alt="X1-STRAIN-qscan_whitened-4.png" class="img-responsive" src="./1126259462/plots/X1-STRAIN-qscan_whitened-4.png" />
</a>
</div>
<div class="col-sm-4">
<a href="./1126259462/plots/X1-STRAIN-qscan_whitened-16.png" id="a_X1-STRAIN_16" title="X1-STRAIN-qscan_whitened-16.png" class="fancybox" target="_blank" data-fancybox-group="images">
<img id="img_X1-STRAIN_16" alt="X1-STRAIN-qscan_whitened-16.png" class="img-responsive" src="./1126259462/plots/X1-STRAIN-qscan_whitened-16.png" />
</a>
</div>
</div>
</div>
</li>
</ul>
</div>"""  # nopep8


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
        'static/bootstrap-ligo.min.css',
        'static/gwdetchar.min.css']
    assert js == [
        'https://code.jquery.com/jquery-1.12.3.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.13.0/'
            'moment.min.js',  # nopep8
        'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/'
            'jquery.fancybox.min.js',  # nopep8
        'static/bootstrap-ligo.min.js',
        'static/gwdetchar.min.js']
    shutil.rmtree(str(tmpdir), ignore_errors=True)


def test_new_bootstrap_page():
    base = os.path.abspath(os.path.curdir)
    page = html.new_bootstrap_page(base=base, refresh=True)
    assert parse_html(str(page)) == parse_html(
        NEW_BOOTSTRAP_PAGE.format(base=base))


def test_navbar():
    navbar = html.navbar(['test'], collapse=False)
    assert parse_html(navbar) == parse_html(
        '<header class="navbar navbar-fixed-top">\n'
        '<div class="container">\n<div class="navbar-header">\n'
        '</div>\n<nav>\n<ul class="nav navbar-nav">\n<li>\ntest\n</li>\n'
        '</ul>\n</nav>\n</div>\n</header>')


def test_dropdown():
    menu = html.dropdown('test', [])
    assert parse_html(str(menu)) == parse_html(
        '<a href="#" class="dropdown-toggle" data-toggle="dropdown">\n'
        'test\n<b class="caret"></b>\n</a>\n<ul class="dropdown-menu">\n</ul>')

    menu = html.dropdown('test', ['test', '#'], active=0)
    assert parse_html(str(menu)) == parse_html(
        '<a href="#" class="dropdown-toggle" data-toggle="dropdown">\n'
        'test\n<b class="caret"></b>\n</a>\n<ul class="dropdown-menu">\n'
        '<li class="active">\ntest\n</li>\n<li>\n#\n</li>\n</ul>')

    menu = html.dropdown('test', ['test', '#'], active=[0, 1])
    assert parse_html(str(menu)) == parse_html(
        '<a href="#" class="dropdown-toggle" data-toggle="dropdown">\n'
        'test\n<b class="caret"></b>\n</a>\n<ul class="dropdown-menu">\n'
        '<li>\ntest\n</li>\n<li>\n#\n</li>\n</ul>')


def test_dropdown_link():
    page = markup.page()
    html.dropdown_link(page, None)
    assert parse_html(str(page)) == parse_html(
        '<li class="divider">\n</li>')

    page = markup.page()
    html.dropdown_link(page, 'test', active=True)
    assert parse_html(str(page)) == parse_html(
        '<li class="active">\ntest\n</li>')

    page = markup.page()
    html.dropdown_link(page, 'test')
    assert parse_html(str(page)) == parse_html(
        '<li>\ntest\n</li>')


def test_get_brand():
    (brand, class_) = html.get_brand('H1', 'Test', 0, about='about')
    assert class_ == 'navbar navbar-fixed-top navbar-h1'
    assert parse_html(brand) == parse_html(
        '<div class="navbar-brand">H1</div>\n'
        '<div class="navbar-brand">Test</div>\n'
        '<div class="btn-group pull-right ifo-links">\n'
        '<a class="navbar-brand dropdown-toggle" href="#" '
        'data-toggle="dropdown">\nLinks\n<b class="caret"></b>\n</a>\n'
        '<ul class="dropdown-menu">\n'
        '<li class="dropdown-header">Internal</li>\n'
        '<li>\n<a href="about">About this page</a>\n</li>\n'
        '<li class="divider"></li>\n'
        '<li class="dropdown-header">External</li>\n'
        '<li>\n<a href="https://ldas-jobs.ligo-wa.caltech.edu/~detchar/'
        'summary/day/19800106" target="_blank">LHO Summary Pages</a>\n'
        '</li>\n<li>\n<a href="https://alog.ligo-wa.caltech.edu/aLOG" '
        'target="_blank">LHO Logbook</a>\n</li>\n</ul>\n</div>')


@mock.patch(
    "gwdetchar.io.html.package_list",
    return_value=[
        {"name": "gwpy", "version": "1.0.0"},
        {"name": "gwdetchar", "version": "1.2.3"},
    ],
)
def test_about_this_page(package_list, tmpdir):
    outdir = str(tmpdir)
    config_file = os.path.join(outdir, 'test.ini')
    with open(config_file, 'w') as fobj:
        fobj.write(TEST_CONFIGURATION)
    testargs = ['/opt/bin/gwdetchar-scattering', '-i', 'X1']
    with mock.patch.object(sys, 'argv', testargs):
        # test with a single config file
        about = html.about_this_page(config_file)
        assert parse_html(about) == parse_html(ABOUT)
        # test with a list of config files
        about = html.about_this_page([config_file])
        assert parse_html(about) == parse_html(ABOUT_WITH_CONFIG_LIST)
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)


def test_write_param():
    page = html.write_param('test', 'test')
    assert parse_html(str(page)) == parse_html(
        '<p>\n<strong>test: </strong>\ntest\n</p>')


def test_get_command_line():
    testargs = ['/opt/bin/gwdetchar-conlog', '-i', 'X1']
    with mock.patch.object(sys, 'argv', testargs):
        cmdline = html.get_command_line()
        assert parse_html(cmdline) == parse_html(
            '<p>This page was generated with the following command-line call:'
            '</p>\n<div class="highlight" style="background: #f8f8f8">'
            '<pre style="line-height: 125%"><span></span>$ gwdetchar-conlog '
            '-i X1\n</pre></div>\n\n<p>The install path used was <code>{}'
            '</code>.</p>'.format(sys.prefix))


def test_get_command_line_module():
    testargs = ['__main__.py', '--html-only']
    with mock.patch.object(sys, 'argv', testargs):
        cmdline = html.get_command_line()
        assert parse_html(cmdline) == parse_html(
            '<p>This page was generated with the following command-line call:'
            '</p>\n<div class="highlight" style="background: #f8f8f8">'
            '<pre style="line-height: 125%"><span></span>$ python -m '
            'gwdetchar.io.tests.test_html\n</pre></div>\n\n'
            '<p>The install path used was <code>{}</code>.</p>'.format(
                sys.prefix))


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
    assert '<h2 id="parameters">Parameters</h2>' in page
    assert '<strong>Start time: </strong>\n0 (1980-01-06 00:00:00)' in page
    assert '<strong>End time: </strong>\n1 (1980-01-06 00:00:01)' in page
    assert '<strong>State flag: </strong>\nX1:TEST' in page
    assert '<strong>test: </strong>\ntest' in page
    assert '<strong>Command-line: </strong>' in page


def test_table():
    headers = ['Test']
    data = [['test']]
    caption = 'This is a test table.'
    page = html.table(headers=headers, data=data, caption=caption, id='test')
    assert parse_html(page) == parse_html(
        '<table class="table table-hover table-condensed table-responsive" '
        'id="test"><caption>This is a test table.</caption><thead><tr>'
        '<th scope="col">Test</th></tr></thead><tbody><tr><td>test</td></tr>'
        '</tbody></table><button class="btn btn-default btn-table" '
        'onclick="exportTableToCSV(&quot;test.csv&quot;, &quot;test&quot;)">'
        'Export to CSV</button>')


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


def test_scaffold_omega_scans():
    times = [1126259462]
    channel = 'X1:STRAIN'
    page = html.scaffold_omega_scans(times, channel)
    assert parse_html(page) == parse_html(OMEGA_SCAFFOLD)


def test_write_footer():
    now = datetime.datetime.now()
    tz = reference.LocalTimezone().tzname(now)
    date = now.strftime('%H:%M {} on %d %B %Y'.format(tz))
    out = html.write_footer()
    assert parse_html(str(out)) == parse_html(
        HTML_FOOTER.format(user=getuser(), date=date))


def test_close_page(tmpdir):
    target = os.path.join(str(tmpdir), 'test.html')
    now = datetime.datetime.now()
    tz = reference.LocalTimezone().tzname(now)
    date = now.strftime('%H:%M {} on %d %B %Y'.format(tz))
    page = html.close_page(html.markup.page(), target)
    assert parse_html(str(page)) == parse_html(
        HTML_CLOSE.format(user=getuser(), date=str(date)))
    assert os.path.isfile(target)
    with open(target, 'r') as fp:
        assert fp.read() == str(page)
    shutil.rmtree(target, ignore_errors=True)


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
        "<h2>Environment</h2><table class=\"test\" id=\"package-table\">"
        "<caption>Test</caption>"
        "<thead>"
        "<tr><th scope=\"col\">Name</th><th scope=\"col\">Version</th></tr>"
        "</thead><tbody>"
        "<tr><td>gwdetchar</td><td>1.2.3</td></tr>"
        "<tr><td>gwpy</td><td>1.0.0</td></tr>"
        "</tbody></table>"
        "<button class=\"btn btn-default btn-table\" "
        "onclick=\"exportTableToCSV(&quot;package-table.csv&quot;, "
        "&quot;package-table&quot;)\">Export to CSV</button>",
    )
