# coding=utf-8
# Copyright (C) Alex Urban (2018-)
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

"""Utilties for writing Omega scan HTML pages
"""

from __future__ import division

import os
import numpy
from functools import wraps
from collections import OrderedDict

from pkg_resources import resource_filename

from MarkupPy import markup

from gwpy.table import Table
from gwpy.time import tconvert

from ..io import html as htmlio

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credit__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# -- give context for ifo names

OBSERVATORY_MAP = {
    'G1': {
        'name': 'GEO',
        'context': 'default',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day/')
        ])
    },
    'H1': {
        'name': 'LIGO Hanford',
        'context': 'danger',
        'links': OrderedDict([
            ('LHO Summary Pages', 'https://ldas-jobs.ligo-wa.caltech.edu/'
                                  '~detchar/summary/day/'),
            ('LHO Logbook', 'https://alog.ligo-wa.caltech.edu/aLOG/')
        ])
    },
    'I1': {
        'name': 'LIGO India',
        'context': 'success',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day/')
        ])
    },
    'K1': {
        'name': 'KAGRA',
        'context': 'warning',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day/'),
            ('KAGRA Logbook', 'http://klog.icrr.u-tokyo.ac.jp/osl/')
        ])
    },
    'L1': {
        'name': 'LIGO Livingston',
        'context': 'info',
        'links': OrderedDict([
            ('LLO Summary Pages', 'https://ldas-jobs.ligo-la.caltech.edu/'
                                  '~detchar/summary/day/'),
            ('LLO Logbook', 'https://alog.ligo-la.caltech.edu/aLOG/')
        ])
    },
    'V1': {
        'name': 'Virgo',
        'context': 'default',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day/'),
            ('Virgo Logbook', 'https://logbook.virgo-gw.eu/virgo/')
        ])
    },
    'Network': {
        'name': 'Multi-IFO',
        'context': 'default',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day/'),
            ('LHO Logbook', 'https://alog.ligo-wa.caltech.edu/aLOG/'),
            ('LLO Logbook', 'https://alog.ligo-la.caltech.edu/aLOG/'),
            ('Virgo Logbook', 'https://logbook.virgo-gw.eu/virgo/'),
            ('KAGRA Logbook', 'http://klog.icrr.u-tokyo.ac.jp/osl/')
        ])
    }
}

# -- set up default JS and CSS files

OMEGA_CSS = resource_filename('gwdetchar', '_static/gwdetchar-omega.min.css')
OMEGA_JS = resource_filename('gwdetchar', '_static/gwdetchar-omega.min.js')

CSS_FILES = htmlio.CSS_FILES + [OMEGA_CSS]
JS_FILES = htmlio.JS_FILES + [OMEGA_JS]


# -- HTML construction --------------------------------------------------------

def init_page(ifo, gpstime, toc={}, refresh=False, css=None, script=None,
              base=os.path.curdir, **kwargs):
    """Initialise a new `markup.page`
    This method constructs an HTML page with the following structure
    .. code-block:: html
        <html>
        <head>
            <!-- some stuff -->
        </head>
        <body>
        <div class="container">
        <div class="page-header">
        <h1>IFO</h1>
        <h3>GPSTIME</h3>
        </div>
        </div>
        <div class="container">

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix
    gpstime : `float`
        the central GPS time of the analysis
    toc : `dict`
        metadata dictionary for navbar table of contents
    refresh : `bool`
        Boolean switch to enable periodic page refresh
    css : `list`, optional
        the list of stylesheets to link in the `<head>`
    script : `list`, optional
        the list of javascript files to link in the `<head>`
    base : `str`, optional, default '.'
        the path for the `<base>` tag to link in the `<head>`

    Returns
    -------
    page : `markup.page`
        the structured markup to open an HTML document
    """
    if not css:
        css = CSS_FILES
    if not script:
        script = JS_FILES

    # write CSS to static dir
    css, script = htmlio.finalize_static_urls(
        os.path.join(os.path.curdir, 'static'),
        css,
        script,
    )

    # create page
    page = markup.page()
    page.header.append('<!DOCTYPE HTML>')
    page.html(lang='en')
    page.head()
    if refresh:
        page.add('<meta http-equiv="refresh" content="60">')
    page.add('<meta content="width=device-width, initial-scale=1.0" '
             'name="viewport">')
    page.base(href=base)
    page._full = True

    # link files
    for f in css:
        page.link(href=f, rel='stylesheet', type='text/css', media='all')
    for f in script:
        page.script('', src=f, type='text/javascript')

    # add other attributes
    for key in kwargs:
        getattr(page, key)(kwargs[key])
    # finalize header
    page.head.close()
    page.body()
    # write banner
    page.add('<header class="navbar navbar-fixed-top navbar-%s">'
             % ifo.lower())
    page.div(class_='container')
    page.div(class_='navbar-header')
    page.add('<button class="navbar-toggle" data-toggle="collapse" '
             'type="button" data-target=".navbar-collapse">')
    page.add('<span class="icon-bar"></span>')
    page.add('<span class="icon-bar"></span>')
    page.add('<span class="icon-bar"></span>')
    page.add('</button>')
    page.div(ifo, class_='navbar-brand')
    page.div(gpstime, class_='navbar-brand')
    page.div.close()  # navbar-header
    page.add('<nav class="collapse navbar-collapse">')
    page.ul(class_='nav navbar-nav')
    page.li('<a href="#">Summary</a>')
    for key, block in toc.items():
        page.li(class_='dropdown')
        page.add('<a class="dropdown-toggle" data-toggle="dropdown">')
        page.add('%s <b class="caret"></b>' % key)
        page.add('</a>')
        page.ul(class_='dropdown-menu', style='max-height: 700px; '
                                              'overflow-y: scroll;')
        page.li(block['name'], class_='dropdown-header')
        for chan in block['channels']:
            page.li()
            chanid = chan.name.lower().replace(':', '-')
            page.a(chan.name, href='#%s' % chanid)
            page.li.close()
        page.ul.close()
        page.li.close()
    page.li(class_='dropdown')
    page.add('<a class="dropdown-toggle" data-toggle="dropdown">')
    page.add('Links <b class="caret"></b>')
    page.add('</a>')
    page.ul(class_='dropdown-menu')
    page.li('Internal', class_='dropdown-header')
    page.li('<a href="about">About this scan</a>')
    page.li('', class_='divider')
    page.li('External', class_='dropdown-header')
    for name, link in OBSERVATORY_MAP[ifo]['links'].items():
        page.li()
        if 'Summary' in name:
            day = str(tconvert(gpstime).date()).replace('-', '')
            link = '/'.join([link, day])
        page.a(name, href=link, target='_blank')
        page.li.close()
    page.ul.close()
    page.li.close()
    page.ul.close()
    page.add('</nav>')
    page.div.close()  # container
    page.add('</header>')  # navbar

    # open container
    page.div(class_='container')
    return page


def close_page(page, target, about=None, date=None):
    """Close an HTML document with markup then write to disk
    This method writes the closing markup to complement the opening
    written by `init_page`, something like:
    .. code-block:: html
       </div>
       <footer>
           <!-- some stuff -->
       </footer>
       </body>
       </html>

    Parameters
    ----------
    page : `markup.page`
        the markup object to close
    target : `str`
        the output filename for HTML
    about : `str`, optional
        the path of the 'about' page to link in the footer
    date : `datetime.datetime`, optional
        the timestamp to place in the footer, defaults to
        `~datetime.datetime.now`
    """
    page.div.close()  # container
    page.add(htmlio.write_footer(about=about, date=date, class_=True,
                                 linkstyle='color:#eee;'))
    if not page._full:
        page.body.close()
        page.html.close()
    with open(target, 'w') as f:
        f.write(page())
    return page


def wrap_html(func):
    """Decorator to wrap a function with `init_page` and `close_page` calls
    This allows inner HTML methods to be written with minimal arguments
    and content, hopefully making things simpler
    """
    @wraps(func)
    def decorated_func(ifo, gpstime, *args, **kwargs):
        # set page init args
        initargs = {
            'title': '%s Qscan | %s' % (ifo, gpstime),
            'base': os.path.curdir,
        }
        for key in ['title', 'base']:
            if key in kwargs:
                initargs[key] = kwargs.pop(key)
        # find outdir
        outdir = kwargs.pop('outdir', initargs['base'])
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        # determine table of contents and refresh options
        toc = kwargs.pop('toc', {})
        refresh = kwargs.pop('refresh', False)
        # determine primary channel
        correlated = kwargs.pop('correlated', False)
        primary = kwargs.pop('primary', '%s:GDS-CALIB_STRAIN' % ifo)
        # write about page
        try:
            config = kwargs.pop('config')
        except KeyError:
            about = None
        else:
            iargs = initargs.copy()
            aboutdir = os.path.join(outdir, 'about')
            if iargs['base'] == os.path.curdir:
                iargs['base'] = os.path.pardir
            iargs['toc'] = toc
            about = write_about_page(ifo, gpstime, config, outdir=aboutdir,
                                     **iargs)
            if os.path.basename(about) == 'index.html':
                about = about[:-10]
        # open page
        page = init_page(ifo, gpstime, toc=toc, refresh=refresh, **initargs)
        # write analysis summary
        # (but only on the main results page)
        if about:
            page.add(write_summary(ifo, gpstime, incomplete=refresh,
                     context=OBSERVATORY_MAP[ifo]['context']))
            write_summary_table(toc, correlated)
            if correlated:
                page.add(write_ranking(toc, primary))
            kwargs['context'] = OBSERVATORY_MAP[ifo]['context']
        # write content
        page.div(id_='main')
        # insert inner html directly
        page.add(str(func(*args, **kwargs)))
        page.div.close()  # main
        # close page
        index = os.path.join(outdir, 'index.html')
        close_page(page, index, about=about)
        return index
    return decorated_func

# -- Utilities ----------------------------------------------------------------

def toggle_link(plottype, channel, pranges):
    """Create a Bootstrap button object that toggles between plot types.

    Parameters
    ----------
    plottype : `str`
        the type of plot to toggle toward
    channel : `OmegaChannel`
        the channel object corresponding to the plots shown
    pranges : `list` of `int`s
        a list of ranges for the time axis of each plot

    Returns
    -------
    page : `page`
        a markup page object
    """
    text = plottype.split('_')[1]
    pstrings = ["'%s'" % p for p in pranges]
    chanstring = channel.name.replace('-', '_').replace(':', '-')
    captions = [p.caption for p in channel.plots[plottype]]
    return markup.oneliner.a(
        text, class_='dropdown-item',
        onclick="showImage('{0}', [{1}], '{2}', {3});".format(
            chanstring, ','.join(pstrings), plottype, captions))


def write_summary_table(blocks, correlated, base=os.path.curdir):
    """Write a summary table in various formats for users to download

    Parameters
    ----------
    blocks : `dict` of `OmegaChannel`
        the channel blocks scanned in the analysis
    correlated : `bool`
        Boolean switch to determine if cross-correlation is included
    base : `str`
        the path for the `<base>` tag to link in the `<head>`
    """
    # record summary data for each channel
    channel, time, freq, Q, energy, snr = ([], [], [], [], [], [])
    if correlated:
        corr, delay = ([], [])
    for block in blocks.values():
        for chan in block['channels']:
            channel.append(chan.name)
            time.append(chan.t)
            freq.append(chan.f)
            Q.append(chan.Q)
            energy.append(chan.energy)
            snr.append(chan.snr)
            if correlated:
                corr.append(chan.corr)
                delay.append(chan.delay)
    # store in a table
    if correlated:
        data = Table([channel, time, freq, Q, energy, snr, corr, delay],
                     names=('Channel', 'Central Time',
                            'Central Frequency (Hz)', 'Q', 'Energy', 'SNR',
                            'Correlation', 'Delay (ms)'))
    else:
        data = Table([channel, time, freq, Q, energy, snr], names=(
            'Channel', 'Central Time', 'Central Frequency (Hz)', 'Q', 'Energy',
            'SNR'))
    # write in several formats
    datadir = os.path.join(base, 'data')
    fname = os.path.join(datadir, 'summary')
    data.write(fname + '.txt', format='ascii', overwrite=True)
    data.write(fname + '.csv', format='csv', overwrite=True)
    data.write(fname + '.tex', format='latex', overwrite=True)


# -- Qscan HTML ---------------------------------------------------------------

def write_summary(
        ifo, gpstime, incomplete=False, context='default', header='Summary',
        tableclass='table table-condensed table-hover table-responsive'):
    """Write the Qscan analysis summary HTML

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix
    gpstime : `float`
        the central GPS time of the analysis
    incomplete : `bool`
        boolean switch to determine whether the scan is still in progress
    context : `str`, optional
        the bootstrap context class for this result, see the bootstrap
        docs for more details
    header : `str`, optional
        the text for the section header (``<h2``>)
    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the formatted markup object containing the analysis summary table
    """
    utc = tconvert(gpstime)
    page = markup.page()
    page.div(class_='banner')
    page.h2(header)
    page.div.close()  # banner
    page.div(class_='row')

    page.div(class_='col-md-5')
    page.table(class_=tableclass)
    # make table body
    page.tbody()
    page.tr()
    page.td("<b>Interferometer</b>", scope='row')
    page.td("%s (%s)" % (OBSERVATORY_MAP[ifo]['name'], ifo))
    page.tr.close()
    page.tr()
    page.td("<b>UTC Time</b>", scope='row')
    page.td("%s" % utc)
    page.tr.close()
    page.tbody.close()
    # close table
    page.table.close()
    page.div.close()  # col-md-5

    # make summary table download button
    page.div(class_='col-xs-12 col-md-7')
    page.div(class_='btn-group', role='group')
    page.button(id_='summary_table_download', type='button',
                class_='btn btn-%s dropdown-toggle' % context,
                **{'data-toggle': 'dropdown'})
    page.add('Download summary <span class="caret"></span>')
    page.button.close()
    page.ul(class_='dropdown-menu', role='menu',
            **{'aria-labelledby': 'summary_table_download'})
    for ext in ['txt', 'csv', 'tex']:
        page.li('<a href="data/summary.%s" download="%s_%s_summary.%s">%s</a>'
                % (ext, ifo, gpstime, ext, ext))
    page.ul.close()
    page.div.close()  # btn-group
    page.div.close()  # col-md-7
    page.div.close()  # row

    # write alert
    if incomplete:
        page.div(class_='row')
        page.div(class_='alert alert-%s' % context)
        page.p('<strong>Note</strong>: This scan is in progress, and will '
               'auto-refresh every 60 seconds until completion.')
        page.div.close()  # alert
        page.div.close()  # row
    return page()


def write_ranking(toc, primary, thresh=6.5,
                  tableclass='table table-condensed table-hover table-bordered'
                             ' table-responsive'):
    """Write a table of channels ranked by their similarity to the primary

    Parameters
    ----------
    toc : `dict`
        metadata dictionary for navbar table of contents
    primary : `str`
        the name of the primary channel
    thresh : `float`
        the minimum correlation amplitude for appearing in this table
    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the formatted markup object containing the analysis summary table
    """
    # construct an ordered dict of channel entries
    entries = OrderedDict([
        ('Channel', numpy.array([c.name for b in toc.values()
                                 for c in b['channels']])),
        ('GPS Time', numpy.array([c.t for b in toc.values()
                                  for c in b['channels']])),
        ('Frequency', numpy.array([c.f for b in toc.values()
                                   for c in b['channels']])),
        ('Q', numpy.array([c.Q for b in toc.values()
                           for c in b['channels']])),
        ('Energy', numpy.array([c.energy for b in toc.values()
                                for c in b['channels']])),
        ('SNR', numpy.array([c.snr for b in toc.values()
                             for c in b['channels']])),
        ('Correlation', numpy.array([c.corr for b in toc.values()
                                     for c in b['channels']])),
        ('Delay', numpy.array([c.delay for b in toc.values()
                               for c in b['channels']]))
    ])
    std = numpy.array([c.stdev for b in toc.values()
                       for c in b['channels']])

    # identify the primary channel
    pind = numpy.nonzero(entries['Channel'] == primary)
    # sort by matched-filter correlation
    ind_sorted = numpy.argsort(entries['Correlation'])[::-1]
    if ind_sorted[0] != pind:
        # prepend the primary channel
        dind = numpy.nonzero(ind_sorted == pind)
        ind_sorted = numpy.delete(ind_sorted, dind)
        ind_sorted = numpy.insert(ind_sorted, 0, pind)

    # construct HTML table
    page = markup.page()
    page.div(class_='row')
    page.div(class_='col-md-12')
    aparams = {
        'title': 'Whitened timeseries of the primary channel, %s.' % primary,
        'class_': 'fancybox',
        'target': '_blank',
        'style': "font-family: Monaco, \"Courier New\", monospace; "
                 "color: black;",
        'data-fancybox-group': 'images',
    }
    tlink = markup.oneliner.a(primary, href='plots/primary.png', **aparams)
    page.p('Below are the top 5 channels ranked by matched-filter correlation '
           'within 100 ms of %s.' % tlink)
    page.table(class_=tableclass)
    page.thead()
    page.tr()
    for column in entries.keys():
        page.th(column, scope='col')
    page.tr.close()
    page.thead.close()
    page.tbody()
    # range over channels
    k = 0
    for i in ind_sorted:
        if k > 5:
            break
        # reject channels with too high a glitch rate
        if (std[i] > 2) and (entries['Channel'][i] != primary):
            continue
        params = {
            'title': entries['Channel'][i],
            'href': '#%s' % entries['Channel'][i].lower().replace(':', '-'),
            'style': "font-family: Monaco, \"Courier New\", monospace; "
                     "color: black;",
        }
        page.tr()
        page.td(markup.oneliner.a(entries['Channel'][i], **params))
        page.td(str(entries['GPS Time'][i]))
        page.td('%.1f Hz' % entries['Frequency'][i])
        page.td(str(entries['Q'][i]))
        page.td(str(entries['Energy'][i]))
        page.td(str(entries['SNR'][i]))
        if entries['Channel'][i] == primary:
            page.td('&mdash;')
            page.td('&mdash;')
        else:
            page.td(str(entries['Correlation'][i]))
            page.td('%s ms' % entries['Delay'][i])
        page.tr.close()
        # increment counter
        k += 1
    page.tbody.close()
    page.table.close()
    page.div.close()  # col-md-12
    page.div.close()  # row
    return page()


def write_block(blockkey, block, context,
                tableclass='table table-condensed table-hover table-bordered '
                           'table-responsive desktop-only'):
    """Write the HTML summary for a specific block of channels

    Parameters
    ----------
    blockkey: `str`
        the key labeling the channel block
    block : `dict` of `OmegaChannel`
        a list of channels and their analysis attributes
    context : `str`
        the type of Bootstrap ``<panel>`` object to use, color-coded by GWO
        standards (must be one of 'default', 'primary', 'success', 'info',
        'warning', or 'danger')
    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the formatted HTML for this block
    """
    page = markup.page()
    page.div(class_='panel panel-%s' % context)
    # -- make heading
    page.div(class_='panel-heading clearfix')
    # link to top of page
    page.div(class_='pull-right')
    if context == 'primary':
        page.a("<small>[top]</small>", href='#', class_='text-light')
    elif context == 'default':
        page.a("<small>[top]</small>", href='#', class_='text-dark')
    else:
        page.a("<small>[top]</small>", href='#', class_='text-%s' % context)
    page.div.close()  # pull-right
    # heading
    page.h3(': '.join([blockkey, block['name']]), class_='panel-title')
    page.div.close()  # panel-heading

    # -- make body
    page.ul(class_='list-group')

    # -- range over channels in this block
    for i, channel in enumerate(block['channels']):
        page.li(class_='list-group-item')
        page.div(class_='container')

        page.div(class_='row')

        # channel name
        chanid = channel.name.lower().replace(':', '-')
        page.h4(htmlio.cis_link(channel.name), id_=chanid)

        page.div(class_='row')

        # summary table
        page.div(class_='col-md-7')
        page.table(class_=tableclass)
        try:
            columns = ['GPS Time', 'Frequency', 'Q', 'Energy', 'SNR',
                       'Correlation', 'Delay']
            entries = [str(channel.t), '%s Hz' % channel.f, str(channel.Q),
                       str(channel.energy), str(channel.snr),
                       str(channel.corr), '%s ms' % channel.delay]
        except:
            columns = ['GPS Time', 'Frequency', 'Q', 'Energy', 'SNR']
            entries = [str(channel.t), '%s Hz' % channel.f, str(channel.Q),
                       str(channel.energy), str(channel.snr)]
        page.thead()
        page.tr()
        for column in columns:
            page.th(column, scope='col')
        page.tr.close()
        page.thead.close()
        page.tbody()
        page.tr()
        for entry in entries:
            page.td(entry)
        page.tr.close()
        page.tbody.close()
        page.table.close()
        page.div.close()  # col-sm-7

        # plot toggle buttons
        page.div(class_='col-xs-12 col-md-5')
        page.div(class_='btn-group', role='group')
        for ptitle, pclass, ptypes in [
            ('Timeseries', 'timeseries', ('raw', 'highpassed', 'whitened')),
            ('Spectrogram', 'qscan', ('highpassed', 'whitened', 'autoscaled')),
            ('Eventgram', 'eventgram', (
                'highpassed', 'whitened', 'autoscaled')),
        ]:
            _id = 'btnGroup{0}{1}'.format(pclass.title(), i)
            page.div(class_='btn-group', role='group')
            page.button(id_=_id, type='button',
                        class_='btn btn-%s dropdown-toggle' % context,
                        **{'data-toggle': 'dropdown'})
            page.add('{0} view <span class="caret"></span>'.format(ptitle))
            page.button.close()
            page.ul(class_='dropdown-menu', role='menu',
                    **{'aria-labelledby': _id})
            for ptype in ptypes:
                page.li(toggle_link('{0}_{1}'.format(pclass, ptype), channel,
                                    channel.pranges))
            page.ul.close()  # dropdown-menu
            page.div.close()  # btn-group
        page.div.close()  # btn-group
        page.div.close()  # col-sm-5

        page.div.close()  # row

        # plots
        page.add(htmlio.scaffold_plots(
            channel.plots['qscan_whitened'],
            nperrow=min(len(channel.pranges), 3)))

        page.div.close()  # container anchor
        page.li.close()

    # close and return
    page.ul.close()
    page.div.close()  # panel
    return page()


# reminder: wrap_html automatically prepends the (ifo, gpstime) args,
# and at least the outdir kwarg, so you should include those in the docstring,
# but not in the actual function declaration - the decorator will take care of
# that for you.

@wrap_html
def write_qscan_page(blocks, context):
    """Write the Qscan results to HTML

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis
    gpstime  : `float`
        the central GPS time of the analysis
    blocks : `dict` of `OmegaChannel`
        the channel blocks scanned in the analysis
    context : `str`, optional
        the type of Bootstrap ``<panel>`` object to use, color-coded by
        GWO standard

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    page = markup.page()
    page.div(class_='banner')
    page.h2('Channel details')
    page.div.close()  # banner
    for key, block in blocks.items():
        page.add(write_block(key, block, context))
    return page


@wrap_html
def write_null_page(reason, context='default'):
    """Write the Qscan results to HTML

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis
    gpstime  : `float`
        the central GPS time of the analysis
    reason : `str`
        the explanation for this null result
    context : `str`, optional
        the bootstrap context class for this result, see the bootstrap
        docs for more details

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    page = markup.page()
    # write alert
    page.div(class_='alert alert-%s' % context)
    page.p(reason)
    page.div.close()  # alert
    return page


@wrap_html
def write_about_page(configfiles):
    """Write a page explaining how a Qscan analysis was completed

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis
    gpstime  : `float`
        the central GPS time of the analysis
    configfiles : `list` of `str`
        list of paths of the configuration files to embed
    outdir : `str`, optional
        the output directory for the HTML

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    # set up page
    page = markup.page()
    page.h2('On the command line')
    page.p('This page was generated with the command line call shown below.')
    page.add(htmlio.get_command_line())
    page.h2('Configuration file')
    page.p('Omega scans are configured with INI-format files. The '
           'configuration files for this analysis are shown below in full.')
    # range over config files
    for configfile in configfiles:
        with open(configfile, 'r') as fobj:
            inifile = fobj.read()
        page.add(htmlio.render_code(inifile, 'ini'))
    # add environment listing
    page.add(str(htmlio.package_table()))
    return page
