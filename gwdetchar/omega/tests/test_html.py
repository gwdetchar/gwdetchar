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

"""Tests for `gwdetchar.omega.html`
"""

import os
import shutil
import datetime
from getpass import getuser

try:  # python 3.x
    from io import StringIO
except ImportError:  # python 2.7
    from cStringIO import StringIO

from .. import (config, html)
from ..._version import get_versions
from ...utils import parse_html

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# global test objects

VERSION = get_versions()['version']
COMMIT = get_versions()['full-revisionid']

HTML_HEADER = """<!DOCTYPE HTML>
<html lang="en">
<head>
<meta http-equiv="refresh" content="60">
<meta content="width=device-width, initial-scale=1.0" name="viewport">
<base href="{base}" />
<link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" rel="stylesheet" type="text/css" media="all" />
<link href="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css" rel="stylesheet" type="text/css" media="all" />
<link href="static/bootstrap-ligo.min.css" rel="stylesheet" type="text/css" media="all" />
<link href="static/gwdetchar-omega.min.css" rel="stylesheet" type="text/css" media="all" />
<script src="https://code.jquery.com/jquery-1.12.3.min.js" type="text/javascript"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.13.0/moment.min.js" type="text/javascript"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js" type="text/javascript"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.js" type="text/javascript"></script>
<script src="static/bootstrap-ligo.min.js" type="text/javascript"></script>
<script src="static/gwdetchar-omega.min.js" type="text/javascript"></script>
</head>
<body>
<header class="navbar navbar-fixed-top navbar-l1">
<div class="container">
<div class="navbar-header">
<button class="navbar-toggle" data-toggle="collapse" type="button" data-target=".navbar-collapse">
<span class="icon-bar"></span>
<span class="icon-bar"></span>
<span class="icon-bar"></span>
</button>
<div class="navbar-brand">{ifo}</div>
<div class="navbar-brand">{gps}</div>
</div>
<nav class="collapse navbar-collapse">
<ul class="nav navbar-nav">
<li><a href="#">Summary</a></li>
<li class="dropdown">
<a class="dropdown-toggle" data-toggle="dropdown">
GW <b class="caret"></b>
</a>
<ul class="dropdown-menu" style="max-height: 700px; overflow-y: scroll;">
<li class="dropdown-header">Gravitational-Wave Strain</li>
<li>
<a href="#x1-test-aux">X1:TEST-AUX</a>
</li>
</ul>
</li>
<li class="dropdown">
<a class="dropdown-toggle" data-toggle="dropdown">
Links <b class="caret"></b>
</a>
<ul class="dropdown-menu">
<li class="dropdown-header">Internal</li>
<li><a href="about">About this scan</a></li>
<li class="divider"></li>
<li class="dropdown-header">External</li>
<li>
<a href="https://ldas-jobs.ligo-la.caltech.edu/~detchar/summary/day//19800106" target="_blank">LLO Summary Pages</a>
</li>
<li>
<a href="https://alog.ligo-la.caltech.edu/aLOG/" target="_blank">LLO Logbook</a>
</li>
</ul>
</li>
</ul>
</nav>
</div>
</header>
<div class="container">
</body>
</html>"""  # nopep8

HTML_CLOSE = """</div>
<footer class="footer">
<div class="container">
<div class="row">
<div class="col-md-12">
<p>These results were obtained using <a style="color:#eee;" href="https://github.com/gwdetchar/gwdetchar/tree/%s" target="_blank">gwdetchar version %s</a> by {user} at {date}.</p>
</div>
</div>
</div>
</footer>
</body>
</html>""" % (COMMIT, VERSION)  # nopep8

CONFIGURATION = u"""
[primary]
; the primary channel, which will be used as a matched-filter
f-low = 4.0
resample = 4096
frametype = X1_HOFT
duration = 64
fftlength = 8
matched-filter-length = 6
channel = X1:TEST-STRAIN

[GW]
; name of this block, which contains h(t)
name = Gravitational Wave Strain
q-range = 3.3166,150.0
frequency-range = 4.0,1024
resample = 4096
frametype = X1_HOFT
state-flag = X1:OBSERVING:1
duration = 64
fftlength = 8
max-mismatch = 0.2
snr-threshold = 5
always-plot = True
plot-time-durations = 4
channels = X1:TEST-AUX
"""

CONFIG_FILE = StringIO(CONFIGURATION)
CP = config.OmegaConfigParser(ifo='X1')
try:  # python 3.x
    CP.read_file(CONFIG_FILE)
except AttributeError:  # python 2.7
    CP.readfp(CONFIG_FILE)
BLOCKS = CP.get_channel_blocks()
PRIMARY = BLOCKS['primary']
GW = BLOCKS['GW']

# set analyzed channel list
ANALYZED = {'GW': {
    'name': 'Gravitational-Wave Strain',
    'channels': GW.channels,
}}
for channel in ANALYZED['GW']['channels']:
    channel.Q = 5
    channel.t = 0
    channel.f = 100
    channel.energy = 1000
    channel.snr = 44.7
    channel.corr = 100
    channel.stdev = 1
    channel.delay = 0

BLOCK_HTML = """<div class="panel panel-info">
<div class="panel-heading clearfix">
<div class="pull-right">
<a href="#" class="text-info"><small>[top]</small></a>
</div>
<h3 class="panel-title">GW: Gravitational-Wave Strain</h3>
</div>
<ul class="list-group">
<li class="list-group-item">
<div class="container">
<div class="row">
<h4 id="x1-test-aux"><a href="https://cis.ligo.org/channel/byname/X1:TEST-AUX" title="CIS entry for X1:TEST-AUX" style="font-family: Monaco, &quot;Courier New&quot;, monospace; color: black;" target="_blank">X1:TEST-AUX</a></h4>
<div class="row">
<div class="col-md-7">
<table class="table table-condensed table-hover table-bordered table-responsive desktop-only">
<thead>
<tr>
<th scope="col">GPS Time</th>
<th scope="col">Frequency</th>
<th scope="col">Q</th>
<th scope="col">Energy</th>
<th scope="col">SNR</th>
<th scope="col">Correlation</th>
<th scope="col">Delay</th>
</tr>
</thead>
<tbody>
<tr>
<td>0</td>
<td>100 Hz</td>
<td>5</td>
<td>1000</td>
<td>44.7</td>
<td>100</td>
<td>0 ms</td>
</tr>
</tbody>
</table>
</div>
<div class="col-xs-12 col-md-5">
<div class="btn-group" role="group">
<div class="btn-group" role="group">
<button id="btnGroupTimeseries0" type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown">
Timeseries view <span class="caret"></span>
</button>
<ul class="dropdown-menu" role="menu" aria-labelledby="btnGroupTimeseries0">
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;timeseries_raw&quot;, [&quot;X1-TEST_AUX-timeseries_raw-4.png&quot;]);">raw</a></li>
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;timeseries_highpassed&quot;, [&quot;X1-TEST_AUX-timeseries_highpassed-4.png&quot;]);">highpassed</a></li>
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;timeseries_whitened&quot;, [&quot;X1-TEST_AUX-timeseries_whitened-4.png&quot;]);">whitened</a></li>
</ul>
</div>
<div class="btn-group" role="group">
<button id="btnGroupQscan0" type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown">
Spectrogram view <span class="caret"></span>
</button>
<ul class="dropdown-menu" role="menu" aria-labelledby="btnGroupQscan0">
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;qscan_highpassed&quot;, [&quot;X1-TEST_AUX-qscan_highpassed-4.png&quot;]);">highpassed</a></li>
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;qscan_whitened&quot;, [&quot;X1-TEST_AUX-qscan_whitened-4.png&quot;]);">whitened</a></li>
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;qscan_autoscaled&quot;, [&quot;X1-TEST_AUX-qscan_autoscaled-4.png&quot;]);">autoscaled</a></li>
</ul>
</div>
<div class="btn-group" role="group">
<button id="btnGroupEventgram0" type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown">
Eventgram view <span class="caret"></span>
</button>
<ul class="dropdown-menu" role="menu" aria-labelledby="btnGroupEventgram0">
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;eventgram_highpassed&quot;, [&quot;X1-TEST_AUX-eventgram_highpassed-4.png&quot;]);">highpassed</a></li>
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;eventgram_whitened&quot;, [&quot;X1-TEST_AUX-eventgram_whitened-4.png&quot;]);">whitened</a></li>
<li><a class="dropdown-item" onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], &quot;eventgram_autoscaled&quot;, [&quot;X1-TEST_AUX-eventgram_autoscaled-4.png&quot;]);">autoscaled</a></li>
</ul>
</div>
</div>
</div>
</div>
<div class="row">
<div class="col-sm-12">
<a href="plots/X1-TEST_AUX-qscan_whitened-4.png" id="a_X1-TEST_AUX_4" title="X1-TEST_AUX-qscan_whitened-4.png" class="fancybox" target="_blank" data-fancybox-group="images">
<img id="img_X1-TEST_AUX_4" alt="X1-TEST_AUX-qscan_whitened-4.png" class="img-responsive" src="plots/X1-TEST_AUX-qscan_whitened-4.png" />
</a>
</div>
</div>
</div>
</li>
</ul>
</div>"""  # nopep8


# -- unit tests ---------------------------------------------------------------

def test_init_page(tmpdir):
    base = str(tmpdir)
    os.chdir(base)
    page = html.init_page('L1', 0, toc=ANALYZED, refresh=True, base=base)
    assert parse_html(str(page)) == parse_html(
        HTML_HEADER.format(base=base, ifo='L1', gps=0))
    shutil.rmtree(base, ignore_errors=True)


def test_close_page(tmpdir):
    # test simple content
    target = os.path.join(str(tmpdir), 'test.html')
    date = datetime.datetime.now()
    page = html.close_page(html.markup.page(), target, date=date)
    assert parse_html(str(page)) == parse_html(
        HTML_CLOSE.format(user=getuser(), date=str(date)))
    assert os.path.isfile(target)
    with open(target, 'r') as fp:
        assert fp.read() == str(page)
    shutil.rmtree(target, ignore_errors=True)


def test_toggle_link():
    h1 = parse_html(html.toggle_link('timeseries_raw', GW.channels[0], [4]))
    h2 = parse_html(
        '<a class="dropdown-item" '
        'onclick="showImage(&quot;X1-TEST_AUX&quot;, [&quot;4&quot;], '
        '&quot;timeseries_raw&quot;, '
        '[&quot;X1-TEST_AUX-timeseries_raw-4.png&quot;]);">raw</a>'
    )
    assert h1 == h2


def test_write_summary_table(tmpdir):
    tmpdir.mkdir('data')
    wdir = str(tmpdir)
    os.chdir(wdir)
    html.write_summary_table(ANALYZED, correlated=True)
    shutil.rmtree(wdir)


def test_write_summary():
    page = html.write_summary('L1', 0, incomplete=True)
    h1 = parse_html(str(page))
    h2 = parse_html(
        '<div class="banner">\n<h2>Summary</h2>\n</div>\n<div class="row">\n'
        '<div class="col-md-5">\n<table class="table table-condensed '
            'table-hover table-responsive">\n<tbody>\n<tr>\n'
        '<td scope="row"><b>Interferometer</b></td>\n<td>LIGO Livingston '
            '(L1)</td>\n</tr>\n<tr>\n<td scope="row"><b>UTC Time</b></td>\n'
        '<td>1980-01-06 00:00:00</td>\n</tr>\n</tbody>\n</table>\n</div>\n'
        '<div class="col-xs-12 col-md-7">\n<div class="btn-group" '
            'role="group">\n<button id="summary_table_download" type="button" '
            'class="btn btn-default dropdown-toggle" data-toggle="dropdown">\n'
            'Download summary <span class="caret"></span>\n</button>\n'
        '<ul class="dropdown-menu" role="menu" '
            'aria-labelledby="summary_table_download">\n'
        '<li><a href="data/summary.txt" download="L1_0_summary.txt">'
            'txt</a></li>\n'
        '<li><a href="data/summary.csv" download="L1_0_summary.csv">'
            'csv</a></li>\n'
        '<li><a href="data/summary.tex" download="L1_0_summary.tex">'
            'tex</a></li>\n'
        '</ul>\n</div>\n</div>\n</div>\n<div class="row">\n'
        '<div class="alert alert-default">\n<p><strong>Note</strong>: '
            'This scan is in progress, and will auto-refresh every 60 seconds '
            'until completion.</p>\n</div>\n</div>'
    )
    assert h1 == h2


def test_write_ranking():
    page = html.write_ranking(ANALYZED, PRIMARY.channel.name)
    h1 = parse_html(str(page))
    h2 = parse_html(
        '<div class="row">\n<div class="col-md-12">\n<p>Below are the top 5 '
            'channels ranked by matched-filter correlation within 100 ms of '
            '<a href="plots/primary.png" title="Whitened timeseries of the '
            'primary channel, X1:TEST-STRAIN." class="fancybox" '
            'target="_blank" style="font-family: Monaco, &quot;Courier '
            'New&quot;, monospace; color: black;" data-fancybox-group='
            '"images">X1:TEST-STRAIN</a>.</p>\n'
        '<table class="table table-condensed table-hover table-bordered '
            'table-responsive">\n'
        '<thead>\n<tr>\n<th scope="col">Channel</th>\n'
        '<th scope="col">GPS Time</th>\n<th scope="col">Frequency</th>\n'
        '<th scope="col">Q</th>\n<th scope="col">Energy</th>\n'
        '<th scope="col">SNR</th>\n<th scope="col">Correlation</th>\n'
        '<th scope="col">Delay</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n'
        '<td><a title="X1:TEST-AUX" href="#x1-test-aux" '
            'style="font-family: Monaco, &quot;Courier New&quot;, monospace; '
            'color: black;">X1:TEST-AUX</a></td>\n'
        '<td>0</td>\n<td>100.0 Hz</td>\n<td>5</td>\n<td>1000</td>\n'
        '<td>44.7</td>\n<td>100</td>\n<td>0 ms</td>\n'
        '</tr>\n</tbody>\n</table>\n</div>\n</div>'
    )
    assert h1 == h2


def test_write_block():
    page = html.write_block('GW', ANALYZED['GW'], 'info')
    assert parse_html(str(page)) == parse_html(BLOCK_HTML)


# -- end-to-end tests ---------------------------------------------------------

def test_write_qscan_page(tmpdir):
    tmpdir.mkdir('about')
    tmpdir.mkdir('data')
    tmpdir.mkdir('plots')
    base = str(tmpdir)
    config = os.path.join(base, 'config.ini')
    with open(config, 'w') as fobj:
        fobj.write(CONFIGURATION)
    os.chdir(base)
    htmlv = {
        'title': 'test',
        'refresh': True,
        'config': [config],
    }
    html.write_qscan_page('L1', 0, ANALYZED, **htmlv)
    html.write_qscan_page('L1', 0, ANALYZED, correlated=False, **htmlv)
    shutil.rmtree(base, ignore_errors=True)


def test_write_null_page(tmpdir):
    os.chdir(str(tmpdir))
    html.write_null_page('L1', 0, 'test', 'info')
    shutil.rmtree(str(tmpdir), ignore_errors=True)


def test_write_about_page(tmpdir):
    base = str(tmpdir)
    config = os.path.join(base, 'config.ini')
    with open(config, 'w') as fobj:
        fobj.write(CONFIGURATION)
    os.chdir(base)
    html.write_about_page('L1', 0, [config], outdir='about')
    shutil.rmtree(base, ignore_errors=True)
