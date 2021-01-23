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

"""Utilties for writing omega scan HTML pages
"""

import os
import numpy
from functools import wraps
from collections import OrderedDict

from MarkupPy import markup

from gwpy.table import Table
from gwpy.time import tconvert

from ..io import html as htmlio

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credit__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# -- HTML construction --------------------------------------------------------

def update_toc(toc, channel, name='GW'):
    """Add a channel to the page table of contents

    Parameters
    ----------
    toc : `dict`
        dictionary used as table of contents for a bootstrap page

    channel : `OmegaChannel`
        channel to be added to `toc`

    name : `str`, optional
        name of a channel's block, default: `'GW'`

    Returns
    -------
    out : `dict`
        the updated dictionary
    """
    out = toc
    try:  # update analyzed dict
        out[channel.section]['channels'].append(channel)
    except KeyError:
        out[channel.section] = {
            'name': name,
            'channels': [channel]}
    return out


def navbar(ifo, gpstime, toc={}):
    """Initialise a new `markup.page`

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix

    gpstime : `float`
        the central GPS time of the analysis

    toc : `dict`
        metadata dictionary for navbar table of contents

    Returns
    -------
    page : `markup.page`
        the structured markup to open an HTML document
    """
    (brand, class_) = htmlio.get_brand(ifo, '&Omega;-scan',
                                       gpstime, about='about')
    # channel navigation
    links = [str(gpstime), ['Summary', '#']]
    for key, block in toc.items():
        channels = [[c.name, '#%s' % c.name.lower().replace(':', '-')]
                    for c in block['channels']]
        links.append([key, [[block['name'], channels]]])
    # return navbar
    return htmlio.navbar(links, brand=brand, class_=class_)


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
            prog = kwargs.pop('prog', None)
            if iargs['base'] == os.path.curdir:
                iargs['base'] = os.path.pardir
            iargs['toc'] = toc
            about = write_about_page(
                ifo, gpstime, config, prog=prog, outdir=aboutdir, **iargs)
            if os.path.basename(about) == 'index.html':
                about = about[:-10]
        # open page
        banner = navbar(ifo, gpstime, toc=toc)
        page = htmlio.new_bootstrap_page(refresh=refresh, navbar=banner,
                                         **initargs)
        # write analysis summary
        # (but only on the main results page)
        if about:
            page.add(write_summary(ifo, gpstime, incomplete=refresh))
            write_summary_table(toc, correlated)
            if correlated:
                page.add(write_ranking(toc, primary))
            kwargs['context'] = ifo.lower()
        # write content
        page.div(id_='main')
        # insert inner html directly
        page.add(str(func(*args, **kwargs)))
        page.div.close()  # main
        # close page
        index = os.path.join(outdir, 'index.html')
        htmlio.close_page(page, index, about=about)
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

    pranges : `list` of `int`
        a list of ranges for the time axis of each plot

    Returns
    -------
    page : `page`
        a markup page object
    """
    text = plottype.split('_')[1]
    pstrings = ["'%s'" % p for p in pranges]
    chanstring = channel.name.replace('-', '_').replace(':', '-')
    captions = ["'%s'" % p.caption for p in channel.plots[plottype]]
    return markup.oneliner.a(
        text, class_='dropdown-item image-switch', **{
            'data-captions': '[%s]' % ','.join(captions),
            'data-channel-name': chanstring,
            'data-image-dir': 'plots',
            'data-image-type': plottype,
            'data-t-ranges': '[%s]' % ','.join(pstrings),
        })


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
        corr, stdev, delay = ([], [], [])
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
                stdev.append(chan.stdev)
                delay.append(chan.delay)
    # store in a table
    if correlated:
        data = Table([channel, time, freq, Q, energy, snr, corr, stdev, delay],
                     names=('Channel', 'Central Time',
                            'Central Frequency (Hz)', 'Q', 'Energy', 'SNR',
                            'Correlation', 'Standard Deviation', 'Delay (ms)'))
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
        ifo, gpstime, incomplete=False, header='Summary',
        tableclass='table table-sm table-hover'):
    """Write the Qscan analysis summary HTML

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix

    gpstime : `float`
        the central GPS time of the analysis

    incomplete : `bool`
        boolean switch to determine whether the scan is still in progress

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
    page.th('Interferometer', scope='row')
    page.td('%s (%s)' % (htmlio.OBSERVATORY_MAP[ifo]['name'], ifo))
    page.tr.close()
    page.tr()
    page.th('UTC Time', scope='row')
    page.td(str(utc))
    page.tr.close()
    page.tbody.close()
    # close table
    page.table.close()
    page.div.close()  # col-md-5

    # make summary table download button
    page.div(class_='col-sm-12 col-md-7')
    content = [(
        ext,
        'data/summary.{}'.format(ext),
        '{0}_{1}_summary.{2}'.format(ifo, gpstime, ext)
    ) for ext in ('txt', 'csv', 'tex')]
    page.add(htmlio.download_btn(
        content, btnclass='btn btn-{} dropdown-toggle'.format(ifo.lower()),
    ))
    page.div.close()  # col-md-7
    page.div.close()  # row

    # write alert
    if incomplete:
        page.add(htmlio.alert(
            ('<strong>Note</strong>: This scan is in progress, and will '
             'auto-refresh every 60 seconds until completion.'),
            context=ifo.lower()))
    return page()


def write_ranking(toc, primary, thresh=6.5,
                  tableclass='table table-sm table-hover table-bordered'):
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
    if not numpy.array_equiv(ind_sorted[0], pind):
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
        'class_': 'fancybox cis-link',
        'data-fancybox': 'gallery',
        'data-fancybox-group': 'images',
        'target': '_blank',
    }
    tlink = markup.oneliner.a(primary, href='plots/primary.png', **aparams)
    page.p('Below are the top 5 channels ranked by matched-filter correlation '
           'within 100 ms of %s.' % tlink)
    # range over channels
    k = 0
    data = []
    for i in ind_sorted:
        if k > 5:
            break
        # reject channels with too high a glitch rate
        if (std[i] > 2) and (entries['Channel'][i] != primary):
            continue
        params = {
            'title': entries['Channel'][i],
            'href': '#%s' % entries['Channel'][i].lower().replace(':', '-'),
            'class_': 'cis-link',
        }
        row = [
            markup.oneliner.a(entries['Channel'][i], **params),
            str(entries['GPS Time'][i]),
            '%.1f Hz' % entries['Frequency'][i],
            str(entries['Q'][i]),
            str(entries['Energy'][i]),
            str(entries['SNR'][i]),
        ]
        if entries['Channel'][i] == primary:
            row.extend(['&mdash;', '&mdash;'])
        else:
            row.extend([str(entries['Correlation'][i]),
                        '%s ms' % entries['Delay'][i]])
        # increment counter
        data.append(row)
        k += 1
    page.add(htmlio.table(
        headers=entries.keys(), data=data, separator='\n', table=tableclass))
    page.div.close()  # col-md-12
    page.div.close()  # row
    return page()


def write_block(blockkey, block, context,
                tableclass='table table-sm table-hover '
                           'table-bordered  d-none d-lg-table'):
    """Write the HTML summary for a specific block of channels

    Parameters
    ----------
    blockkey: `str`
        the key labeling the channel block

    block : `dict` of `OmegaChannel`
        a list of channels and their analysis attributes

    context : `str`
        the type of Bootstrap ``<card>`` object to use, color-coded by GWO
        standards (must be one of 'h1', 'l1', 'v1', 'k1', 'i1', 'g1', or
        'network')

    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the formatted HTML for this block
    """
    page = markup.page()
    page.div(class_='card card-%s mb-5 shadow-sm' % context)
    # -- make heading
    page.div(class_='card-header pb-0')
    page.h5(': '.join([blockkey, block['name']]), class_='card-title')
    page.div.close()  # card-header pb-0

    # -- make body
    page.div(class_='card-body')
    page.div(class_='list-group')

    # -- range over channels in this block
    for i, channel in enumerate(block['channels']):
        page.div(class_='list-group-item flex-column align-items-start')

        # channel name
        chanid = channel.name.lower().replace(':', '-')
        page.h5(htmlio.cis_link(channel.name), class_='card-title', id_=chanid)

        # summary table
        page.div(class_='row')
        page.div(class_='col-sm-12 col-md-7')
        try:
            columns = ['GPS Time', 'Frequency', 'Q', 'Energy', 'SNR',
                       'Correlation', 'Delay']
            entries = [[str(channel.t), '%s Hz' % channel.f, str(channel.Q),
                        str(channel.energy), str(channel.snr),
                        str(channel.corr), '%s ms' % channel.delay]]
        except AttributeError:
            columns = ['GPS Time', 'Frequency', 'Q', 'Energy', 'SNR']
            entries = [[str(channel.t), '%s Hz' % channel.f, str(channel.Q),
                        str(channel.energy), str(channel.snr)]]
        page.add(
            htmlio.table(columns, entries, separator='\n', table=tableclass))
        page.div.close()  # col-sm-12 col-md-7

        # plot toggle buttons
        page.div(class_='col-sm-12 col-md-5')
        page.div(class_='btn-group flex-wrap', role='group')
        for ptitle, pclass, ptypes in [
            ('Timeseries', 'timeseries', ('raw', 'highpassed', 'whitened')),
            ('Spectrogram', 'qscan', ('highpassed', 'whitened', 'autoscaled')),
            ('Eventgram', 'eventgram', (
                'highpassed', 'whitened', 'autoscaled')),
        ]:
            _id = 'btnGroup{0}{1}'.format(pclass.title(), i)
            page.div(class_='btn-group', role='group')
            page.button(ptitle, id_=_id, type='button',
                        class_='btn btn-%s dropdown-toggle' % context,
                        **{'data-toggle': 'dropdown'})
            page.div(class_='dropdown-menu shadow', **{'aria-labelledby': _id})
            for ptype in ptypes:
                page.add(toggle_link('{0}_{1}'.format(pclass, ptype),
                                     channel, channel.pranges))
            page.div.close()  # dropdown-menu
            page.div.close()  # btn-group
        page.div.close()  # btn-group
        page.div.close()  # col-sm-12 col-md-5
        page.div.close()  # row

        # plots
        page.add(htmlio.scaffold_plots(
            channel.plots['qscan_whitened'],
            nperrow=min(len(channel.pranges), 3)))

        page.div.close()  # list-group-item

    # close and return
    page.div.close()  # list-group
    page.div.close()  # card-body
    page.div.close()  # card
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
        the type of Bootstrap ``<card>`` object to use, color-coded by
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
def write_null_page(reason, context='info'):
    """Write the Qscan results to HTML

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis

    gpstime  : `float`
        the central GPS time of the analysis

    reason : `str`
        the explanation for this null result

    context : `str`
        type of bootstrap alert box to use, default: ``info``

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    page = markup.page()
    page.add(htmlio.alert(reason, context=context, dismiss=False))
    return page


@wrap_html
def write_about_page(configfiles, prog=None):
    """Write a page explaining how a Qscan analysis was completed

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis

    gpstime  : `float`
        the central GPS time of the analysis

    configfiles : `list` of `str`
        list of paths of the configuration files to embed

    prog : `str`, optional
        name of the program which produced this page, defaults to
        the script run on the command-line

    outdir : `str`, optional
        the output directory for the HTML

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    # set up page
    return htmlio.about_this_page(
        configfiles[0] if len(configfiles) == 1 else configfiles,
        prog=prog,
    )
