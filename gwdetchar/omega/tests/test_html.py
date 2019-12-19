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
from io import StringIO

from .. import (config, html)
from ..._version import get_versions
from ...utils import parse_html

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# global test objects

VERSION = get_versions()['version']
COMMIT = get_versions()['full-revisionid']

HTML_HEADER = """<nav class="navbar fixed-top navbar-expand-md navbar-{ifo} shadow-sm">
<div class="container-fluid">
<div class="navbar-brand border border-white rounded">{IFO} &Omega;-scan</div>
<button class="navbar-toggler navbar-toggler-right" type="button" data-toggle="collapse" data-target=".navbar-collapse">
<span class="navbar-toggler-icon"></span>
</button>
<div class="collapse navbar-collapse justify-content-between">
<ul class="nav navbar-nav mr-auto">
<li class="nav-item navbar-text">
0
</li>
<li class="nav-item">
<a href="#" class="nav-link">Summary</a>
</li>
<li class="nav-item dropdown">
<a href="#" class="nav-link dropdown-toggle" role="button" data-toggle="dropdown">GW</a>
<div class="dropdown-menu dropdown-1-col shadow">
<div class="row">
<div class="col-sm-12 col-md-12">
<h6 class="dropdown-header">Gravitational-Wave Strain</h6>
<a href="#x1-test-aux" class="dropdown-item">X1:TEST-AUX</a>
</div>
</div>
</div>
</li>
</ul>
<ul class="nav navbar-nav">
<li class="nav-item dropdown">
<a class="nav-link dropdown-toggle" href="#" role="button" data-toggle="dropdown">Links</a>
<div class="dropdown-menu dropdown-menu-right shadow">
<h6 class="dropdown-header">Internal</h6>
<a href="about" class="dropdown-item">About this page</a>
<div class="dropdown-divider"></div>
<h6 class="dropdown-header">External</h6>
<a href="https://ldas-jobs.ligo-la.caltech.edu/~detchar/summary/day/19800106" class="dropdown-item" target="_blank">LLO Summary Pages</a>
<a href="https://alog.ligo-la.caltech.edu/aLOG" class="dropdown-item" target="_blank">LLO Logbook</a>
</div>
</li>
</ul>
</div>
</div>
</nav>"""  # noqa: E501

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
name = Gravitational-Wave Strain
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
CP.read_file(CONFIG_FILE)
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

BLOCK_HTML = """<div class="card card-x1 mb-5 shadow-sm">
<div class="card-header pb-0">
<h5 class="card-title">GW: Gravitational-Wave Strain</h5>
</div>
<div class="card-body">
<div class="list-group">
<div class="list-group-item flex-column align-items-start">
<h5 class="card-title" id="x1-test-aux"><a class="cis-link" href="https://cis.ligo.org/channel/byname/X1:TEST-AUX" title="CIS entry for X1:TEST-AUX" target="_blank">X1:TEST-AUX</a></h5>
<div class="row">
<div class="col-sm-12 col-md-7">
<table class="table table-sm table-hover table-bordered  d-none d-lg-table">
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
<div class="col-sm-12 col-md-5">
<div class="btn-group flex-wrap" role="group">
<div class="btn-group" role="group">
<button id="btnGroupTimeseries0" type="button" class="btn btn-x1 dropdown-toggle" data-toggle="dropdown">Timeseries</button>
<div class="dropdown-menu shadow" aria-labelledby="btnGroupTimeseries0">
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-timeseries_raw-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="timeseries_raw" data-t-ranges="[&quot;4&quot;]">raw</a>
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-timeseries_highpassed-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="timeseries_highpassed" data-t-ranges="[&quot;4&quot;]">highpassed</a>
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-timeseries_whitened-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="timeseries_whitened" data-t-ranges="[&quot;4&quot;]">whitened</a>
</div>
</div>
<div class="btn-group" role="group">
<button id="btnGroupQscan0" type="button" class="btn btn-x1 dropdown-toggle" data-toggle="dropdown">Spectrogram</button>
<div class="dropdown-menu shadow" aria-labelledby="btnGroupQscan0">
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-qscan_highpassed-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="qscan_highpassed" data-t-ranges="[&quot;4&quot;]">highpassed</a>
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-qscan_whitened-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="qscan_whitened" data-t-ranges="[&quot;4&quot;]">whitened</a>
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-qscan_autoscaled-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="qscan_autoscaled" data-t-ranges="[&quot;4&quot;]">autoscaled</a>
</div>
</div>
<div class="btn-group" role="group">
<button id="btnGroupEventgram0" type="button" class="btn btn-x1 dropdown-toggle" data-toggle="dropdown">Eventgram</button>
<div class="dropdown-menu shadow" aria-labelledby="btnGroupEventgram0">
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-eventgram_highpassed-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="eventgram_highpassed" data-t-ranges="[&quot;4&quot;]">highpassed</a>
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-eventgram_whitened-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="eventgram_whitened" data-t-ranges="[&quot;4&quot;]">whitened</a>
<a class="dropdown-item image-switch" data-captions="[&quot;X1-TEST_AUX-eventgram_autoscaled-4.png&quot;]" data-channel-name="X1-TEST_AUX" data-image-dir="plots" data-image-type="eventgram_autoscaled" data-t-ranges="[&quot;4&quot;]">autoscaled</a>
</div>
</div>
</div>
</div>
</div>
<div class="row scaffold">
<div class="col-sm-12">
<a href="plots/X1-TEST_AUX-qscan_whitened-4.png" id="a_X1-TEST_AUX_4" title="X1-TEST_AUX-qscan_whitened-4.png" class="fancybox" target="_blank" data-caption="X1-TEST_AUX-qscan_whitened-4.png" data-fancybox="gallery" data-fancybox-group="images">
<img id="img_X1-TEST_AUX_4" alt="X1-TEST_AUX-qscan_whitened-4.png" class="img-fluid w-100 lazy" data-src="plots/X1-TEST_AUX-qscan_whitened-4.png" />
</a>
</div>
</div>
</div>
</div>
</div>
</div>"""  # noqa: E501


# -- unit tests ---------------------------------------------------------------

def test_update_toc():
    toc = html.update_toc(dict(), GW.channels[0], GW.name)
    assert toc.keys() == ANALYZED.keys()
    assert toc['GW'].keys() == ANALYZED['GW'].keys()
    assert len(toc['GW']['channels']) == len(ANALYZED['GW']['channels'])
    assert toc['GW']['channels'][0].name == ANALYZED['GW']['channels'][0].name
    assert toc['GW']['name'] == ANALYZED['GW']['name']


def test_navbar():
    page = html.navbar('L1', 0, toc=ANALYZED)
    assert parse_html(str(page)) == parse_html(HTML_HEADER.format(
        ifo='l1', IFO='L1'))


def test_toggle_link():
    h1 = parse_html(html.toggle_link('timeseries_raw', GW.channels[0], [4]))
    h2 = parse_html(
        '<a class="dropdown-item image-switch" data-captions='
        '"[&quot;X1-TEST_AUX-timeseries_raw-4.png&quot;]" '
        'data-channel-name="X1-TEST_AUX" data-image-dir="plots" '
        'data-image-type="timeseries_raw" data-t-ranges="[&quot;4&quot;]">'
        'raw</a>'
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
    assert parse_html(str(page)) == parse_html(
        '<div class="banner">\n<h2>Summary</h2>\n</div>\n<div class="row">'
        '\n<div class="col-md-5">\n<table class="table table-sm table-hover">'
        '\n<tbody>\n<tr>\n<th scope="row">Interferometer</th>'
        '\n<td>LIGO Livingston (L1)</td>\n</tr>\n<tr>'
        '\n<th scope="row">UTC Time</th>\n<td>1980-01-06 00:00:00</td>'
        '\n</tr>\n</tbody>\n</table>\n</div>\n<div class="col-sm-12 col-md-7">'
        '\n<div class="dropdown float-right d-none d-lg-block">'
        '\n<button type="button" class="btn btn-l1 dropdown-toggle" '
        'data-toggle="dropdown" aria-expanded="false" aria-haspopup="true">'
        'Download summary</button>\n<div class="dropdown-menu dropdown-menu-'
        'right shadow">\n<a href="data/summary.txt" download="L1_0_summary.txt'
        '" class="dropdown-item">txt</a>\n<a href="data/summary.csv" download='
        '"L1_0_summary.csv" class="dropdown-item">csv</a>'
        '\n<a href="data/summary.tex" download="L1_0_summary.tex" '
        'class="dropdown-item">tex</a>\n</div>\n</div>\n</div>\n</div>'
        '\n<div class="alert alert-l1 alert-dismissible fade show text-justify'
        ' shadow-sm">\n<button type="button" class="close" data-dismiss='
        '"alert"aria-label="Close">\n<span aria-hidden="true">&times;</span>\n'
        '</button>\n<strong>Note</strong>: This scan is in progress, and will '
        'auto-refresh every 60 seconds until completion.\n</div>')


def test_write_ranking():
    page = html.write_ranking(ANALYZED, PRIMARY.channel.name)
    h1 = parse_html(str(page))
    h2 = parse_html(
        '<div class="row">\n<div class="col-md-12">\n<p>Below are the top 5 '
        'channels ranked by matched-filter correlation within 100 ms of <a '
        'href="plots/primary.png" title="Whitened timeseries of the primary '
        'channel, X1:TEST-STRAIN." class="fancybox cis-link" target="_blank"'
        'data-fancybox="gallery" data-fancybox-group="images">X1:TEST-STRAIN'
        '</a>.</p>\n<table class="table table-sm table-hover table-bordered"'
        '>\n<thead>\n<tr>\n<th scope="col">Channel</th>\n<th scope="col">GPS'
        ' Time</th>\n<th scope="col">Frequency</th>\n<th scope="col">Q</th>'
        '\n<th scope="col">Energy</th>\n<th scope="col">SNR</th>'
        '\n<th scope="col">Correlation</th>\n<th scope="col">Delay</th>'
        '\n</tr>\n</thead>\n<tbody>\n<tr>\n<td><a title="X1:TEST-AUX" '
        'class="cis-link" href="#x1-test-aux">X1:TEST-AUX</a></td>'
        '\n<td>0</td>\n<td>100.0 Hz</td>\n<td>5</td>\n<td>1000</td>'
        '\n<td>44.7</td>\n<td>100</td>\n<td>0 ms</td>\n</tr>\n</tbody>'
        '\n</table>\n</div>\n</div>'
    )
    assert h1 == h2


def test_write_block():
    page = html.write_block('GW', ANALYZED['GW'], 'x1')
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
    html.write_null_page('L1', 0, 'test')
    shutil.rmtree(str(tmpdir), ignore_errors=True)


def test_write_about_page(tmpdir):
    base = str(tmpdir)
    config = os.path.join(base, 'config.ini')
    with open(config, 'w') as fobj:
        fobj.write(CONFIGURATION)
    os.chdir(base)
    html.write_about_page('L1', 0, [config], outdir='about')
    shutil.rmtree(base, ignore_errors=True)
