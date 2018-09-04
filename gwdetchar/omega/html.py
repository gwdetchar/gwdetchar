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

"""Utilties for writing Omega scan HTML pages
"""

from __future__ import division

import os
import sys
import datetime
import subprocess
from functools import wraps
from getpass import getuser

from glue import markup
from gwpy.time import tconvert
from gwpy.plotter.colors import GW_OBSERVATORY_COLORS
from ..io.html import (JQUERY_JS, BOOTSTRAP_CSS, BOOTSTRAP_JS)
from .. import __version__

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credit__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# -- give context for ifo names

OBSERVATORY_MAP = {
    'G1': {
        'name': 'GEO',
        'context': 'default'
    },
    'H1': {
        'name': 'LIGO Hanford',
        'context': 'danger'
    },
    'I1': {
        'name': 'LIGO India',
        'context': 'success'
    },
    'K1': {
        'name': 'KAGRA',
        'context': 'warning'
    },
    'L1': {
        'name': 'LIGO Livingston',
        'context': 'info'
    },
    'V1': {
        'name': 'Virgo',
        'context': 'primary'
    }
}

# -- set up default JS and CSS files

FANCYBOX_CSS = (
    "//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css")
FANCYBOX_JS = (
    "//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.js")

CSS_FILES = [BOOTSTRAP_CSS, FANCYBOX_CSS]
JS_FILES = [JQUERY_JS, BOOTSTRAP_JS, FANCYBOX_JS]

OMEGA_CSS = """
html {
		position: relative;
		min-height: 100%;
}
body {
		padding-top: 75px;
		margin-bottom: 120px;
		min-height: 100%;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		-webkit-font-smoothing: antialiased;
}
.navbar {
		color: #eee;
		padding-top: 8px;
		padding-bottom: 8px;
		-moz-box-shadow:    0 1px 10px 2px #ccc;
		-webkit-box-shadow: 0 1px 10px 2px #ccc;
		box-shadow:         0 1px 10px 2px #ccc;
}
.with-margin {
		margin-bottom: 15px;
}
.footer {
		position: absolute;
		bottom: 0;
		width: 100%;
		height: 100px;
		color: #eee;
		background-color: #4c4c4c;
		padding-top: 20px;
		padding-bottom: 20px;
}
.fancybox-skin {
		background: white;
}
"""  # nopep8

OMEGA_JS = """
$(document).ready(function() {
	$(\".fancybox\").fancybox({
		nextEffect: 'none',
		prevEffect: 'none',
		helpers: {title: {type: 'inside'}}
	});
});
function showImage(channelName, tRanges, imageType, captions) {
	for (var tIndex in tRanges) {
		var idBase = channelName + "_" + tRanges[tIndex];
		var fileBase = channelName + "-" + imageType + "-" + tRanges[tIndex];
		document.getElementById("a_" + idBase).href =
			"plots/" + fileBase + ".png";
		document.getElementById("a_" + idBase).title = captions[tIndex];
		document.getElementById("img_" + idBase).src =
			"plots/" + fileBase + ".png";
		document.getElementById("img_" + idBase).alt = fileBase + ".png";
	};
};
"""  # nopep8


# -- Plot construction --------------------------------------------------------

class FancyPlot(object):
    """A helpful class of objects that coalesce image links and caption text
    for fancybox figures.

    Parameters
    ----------
    img : `str` or `FancyPlot`
        either a filename (including relative or absolute path) or another
        FancyPlot instance
    caption : `str`
        the text to be displayed in a fancybox as this figure's caption
    """
    def __init__(self, img, caption=None):
        if isinstance(img, FancyPlot):
            caption = caption if caption else img.caption
        self.img = str(img)
        self.caption = caption if caption else os.path.basename(self.img)

    def __str__(self):
        return self.img


# -- HTML construction --------------------------------------------------------

def write_static_files(static):
    """Write static CSS and javascript files into the given directory

    Parameters
    ----------
    static : `str`
        the target directory for the static files, will be created if
        necessary

    Returns
    -------
    `<statc>/omega.css`
    `<static>/omega.js`
        the paths of the two files written by this method, which will be
        `omega.css` and `omega.js` inside `static`

    Notes
    -----
    This method modifies the module-level variables ``CSS_FILES`` and
    ``JS_FILES`` to guarantee that the static files are actually only
    written once per process.
    """
    if not os.path.isdir(static):
        os.makedirs(static)
    omegacss = os.path.join(static, 'omega.css')
    if omegacss not in CSS_FILES:
        with open(omegacss, 'w') as f:
            f.write(OMEGA_CSS)
        CSS_FILES.append(omegacss)
    omegajs = os.path.join(static, 'omega.js')
    if omegajs not in JS_FILES:
        with open(omegajs, 'w') as f:
            f.write(OMEGA_JS)
        JS_FILES.append(omegajs)
    return omegacss, omegajs


def init_page(ifo, gpstime, css=[], script=[], base=os.path.curdir,
              **kwargs):
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
    # write CSS to static dir
    staticdir = os.path.join(os.path.curdir, 'static')
    write_static_files(staticdir)
    # create page
    page = markup.page()
    page.header.append('<!DOCTYPE HTML>')
    page.html(lang='en')
    page.head()
    page.base(href=base)
    page._full = True
    # link stylesheets (appending bootstrap if needed)
    css = css[:]
    for cssf in CSS_FILES[::-1]:
        b = os.path.basename(cssf)
        if not any(f.endswith(b) for f in css):
            css.insert(0, cssf)
    for f in css:
        page.link(href=f, rel='stylesheet', type='text/css', media='all')
    # link javascript
    script = script[:]
    for jsf in JS_FILES[::-1]:
        b = os.path.basename(jsf)
        if not any(f.endswith(b) for f in script):
            script.insert(0, jsf)
    for f in script:
        page.script('', src=f, type='text/javascript')
    # add other attributes
    for key in kwargs:
        getattr(page, key)(kwargs[key])
    # finalize header
    page.head.close()
    page.body()
    # write banner
    page.div(class_='navbar navbar-fixed-top', role='banner',
             style='background-color:%s;' % GW_OBSERVATORY_COLORS[ifo])
    page.div(class_='container')
    page.h4('%s Omega Scan <span style="float:right;">%s</span>'
            % (ifo, gpstime), style="text-align:left;")
    page.div.close()  # container
    page.div.close()  # navbar

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
    page.add(str(write_footer(about=about, date=date)))
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
            about = write_about_page(ifo, gpstime, config, outdir=aboutdir,
                                     **iargs)
            if os.path.basename(about) == 'index.html':
                about = about[:-10]
        # open page
        page = init_page(ifo, gpstime, **initargs)
        # write analysis summary
        # (but only on the main results page)
        if about:
            page.add(write_summary(ifo, gpstime))
            kwargs['context'] = OBSERVATORY_MAP[ifo]['context']
        # write content
        contentf = os.path.join(outdir, '_inner.html')
        with open(contentf, 'w') as f:
            f.write(str(func(*args, **kwargs)))
        # embed content
        page.div('', id_='content')
        page.script("$('#content').load('%s');" % contentf)
        # close page
        index = os.path.join(outdir, 'index.html')
        close_page(page, index, about=about)
        return index
    return decorated_func

# -- Utilities ----------------------------------------------------------------


def html_link(href, txt, target="_blank", **params):
    """Write an HTML <a> tag

    Parameters
    ----------
    href : `str`
        the URL to point to
    txt : `str`
        the text for the link
    target : `str`, optional
        the ``target`` of this link
    **params
        other HTML parameters for the ``<a>`` tag

    Returns
    -------
    html : `str`
    """
    if target is not None:
        params.setdefault('target', target)
    return markup.oneliner.a(txt, href=href, **params)


def toggle_button(plottype, channel, pranges, context):
    """Create a Bootstrap button object that toggles between plot types.

    Parameters
    ----------
    plottype : `str`
        the type of plot to toggle toward
    channel : `OmegaChannel`
        the channel object corresponding to the plots shown
    pranges : `list` of `int`s
        a list of ranges for the time axis of each plot
    context : `str`
        the Bootstrap context that controls color-coding

    Returns
    -------
    page : `page`
        a markup page object
    """
    page = markup.page()
    text = plottype.split('_')[1]
    pstrings = ["'%s'" % p for p in pranges]
    chanstring = channel.name.replace('-', '_').replace(':', '-')
    captions = [p.caption for p in channel.plots[plottype]]
    page.button('<b>%s</b>' % text, type_='button',
                class_='btn btn-%s' % context, style='opacity:0.6;',
                onclick=u"showImage('%s', [%s], '%s', %s);"
                        % (chanstring, ','.join(pstrings), plottype, captions))
    return page()


def cis_link(channel, **params):
    """Write a channel name as a link to the Channel Information System

    Parameters
    ----------
    channel : `str`
        the name of the channel to link
    **params
        other HTML parmeters for the ``<a>`` tag

    Returns
    -------
    html : `str`
    """
    kwargs = {
        'title': "CIS entry for %s" % channel,
        'style': "font-family: Monaco, \"Courier New\", monospace;",
    }
    kwargs.update(params)
    return html_link("https://cis.ligo.org/channel/byname/%s" % channel,
                     channel, **kwargs)


def fancybox_img(img, linkparams=dict(), **params):
    """Return the markup to embed an <img> in HTML

    Parameters
    ----------
    img : `FancyPlot`
        a `FancyPlot` object containing the path of the image to embed
        and its caption to be displayed
    linkparams : `dict`
        the HTML attributes for the ``<a>`` tag
    **params
        the HTML attributes for the ``<img>`` tag

    Returns
    -------
    html : `str`
    Notes
    -----
    See `~gwdetchar.omega.plot.FancyPlot` for more about the `FancyPlot` class.
    """
    page = markup.page()
    aparams = {
        'title': img.caption,
        'class_': 'fancybox',
        'target': '_blank',
        'data-fancybox-group': 'qscan-image',
    }
    aparams.update(linkparams)
    img = str(img)
    substrings = os.path.basename(img).split('-')
    channel = '%s-%s' % tuple(substrings[:2])
    duration = substrings[-1].split('.')[0]
    page.a(href=img, id_='a_%s_%s' % (channel, duration), **aparams)
    imgparams = {
        'alt': os.path.basename(img),
        'class_': 'img-responsive',
    }
    imgparams['src'] = img
    imgparams.update(params)
    page.img(id_='img_%s_%s' % (channel, duration), **imgparams)
    page.a.close()
    return str(page)


def scaffold_plots(plots, nperrow=2):
    """Embed a `list` of images in a bootstrap scaffold

    Parameters
    ----------
    plot : `list` of `FancyPlot`
        the list of image paths to embed
    nperrow : `int`
        the number of images to place in a row (on a desktop screen)

    Returns
    -------
    page : `~glue.markup.page`
        the markup object containing the scaffolded HTML
    """
    page = markup.page()
    x = int(12//nperrow)
    # scaffold plots
    for i, p in enumerate(plots):
        if i % nperrow == 0:
            page.div(class_='row', style="width:96%;")
        page.div(class_='col-sm-%d' % x)
        page.add(fancybox_img(p))
        page.div.close()  # col
        if i % nperrow == nperrow - 1:
            page.div.close()  # row
    if i % nperrow < nperrow-1:
        page.div.close()  # row
    return page()


def write_footer(about=None, date=None):
    """Write a <footer> for a Qscan page

    Parameters
    ----------
    about : `str`, optional
        path of about page to link
    date : `datetime.datetime`, optional
        the datetime representing when this analysis was generated, defaults
        to `~datetime.datetime.now`

    Returns
    -------
    page : `~glue.markup.page`
        the markup object containing the footer HTML
    """
    page = markup.page()
    page.twotags.append('footer')
    markup.element('footer', case=page.case, parent=page)(class_='footer')
    page.div(class_='container')
    # write user/time for analysis
    if date is None:
        date = datetime.datetime.now().replace(second=0, microsecond=0)
    version = __version__
    url = 'https://github.com/ligovirgo/gwdetchar'
    hlink = markup.oneliner.a('GW-DetChar version %s' % version, href=url,
                              target='_blank', style='color:#eee;')
    page.p('Page generated using %s by %s at %s'
           % (hlink, getuser(), date))
    # link to 'about'
    if about is not None:
        page.a('How was this page generated?', href=about, style='color:#eee;')
    page.div.close()  # container
    markup.element('footer', case=page.case, parent=page).close()
    return page


def write_config_html(filepath, format='ini'):
    """Return an HTML-formatted copy of the file with syntax highlighting
    This method attemps to use the `highlight` package to provide a block
    of HTML that can be embedded inside a ``<pre></pre>`` tag.

    Parameters
    ----------
    filepath : `str`
        path of file to format
    format : `str`, optional
        syntax format for this file

    Returns
    -------
    html : `str`
        a formatted block of HTML containing HTML with inline CSS
    """
    highlight = ['highlight', '--out-format', 'html', '--syntax', format,
                 '--inline-css', '--fragment', '--input', filepath]
    try:
        process = subprocess.Popen(highlight, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError:
        with open(filepath, 'r') as fobj:
            return fobj.read()
    else:
        out, err = process.communicate()
        if process.returncode != 0:
            with open(filepath, 'r') as fobj:
                return fobj.read()
        else:
            return out


# -- Qscan HTML ---------------------------------------------------------------

def write_summary(
        ifo, gpstime, header='Analysis Summary',
        tableclass='table table-condensed table-hover table-responsive'):
    """Write the Qscan analysis summary HTML

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix
    gpstime : `float`
        the central GPS time of the analysis
    header : `str`, optional
        the text for the section header (``<h2``>)
    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``

    Returns
    -------
    page : `~glue.markup.page`
        the formatted markup object containing the analysis summary table
    """
    utc = tconvert(gpstime)
    page = markup.page()
    page.h2(header)
    page.p('This page shows time-frequency maps of a user-configured list of '
           'channels for a given interferometer and GPS time. Time-frequency '
           'maps are computed using the <a '
           'href="https://gwpy.github.io/docs/stable/examples/timeseries/'
           'qscan.html" target="_blank">Q-transform</a>.')
    page.p("This analysis is based on the following run arguments.")
    page.table(class_=tableclass)
    # make table body
    page.tbody()
    page.tr()
    page.td("<b>Interferometer</b>")
    page.td("%s (%s)" % (OBSERVATORY_MAP[ifo]['name'], ifo))
    page.tr.close()
    page.tr()
    page.td("<b>UTC Time</b>")
    page.td("%s" % utc)
    page.tr.close()
    page.tbody.close()
    # close table
    page.table.close()
    return page()


def write_toc(blocks):
    """Write the HTML table of contents for ease of navigation

    Parameters
    ----------
    blocks : `list` of `OmegaChannelList`
        the channel blocks scanned in the analysis

    Returns
    -------
    page : `~glue.markup.page`
        the formatted HTML for a table of contents
    """
    page = markup.page()
    page.div(class_="container")
    page.h2('Table of Contents')
    page.ul()
    for i, block in enumerate(blocks):
        page.li()
        page.a('%s' % block.name, href='#block-%s' % block.key)
        page.li.close()
    page.ul.close()
    page.div.close()
    return page()


def write_block(block, context, tableclass='table table-condensed table-hover '
                                           'table-responsive'):
    """Write the HTML summary for a specific block of channels

    Parameters
    ----------
    block : `OmegaChannelList`
        a list of channels and their analysis attributes
    context : `str`
        the type of Bootstrap ``<panel>`` object to use, color-coded by GWO
        standards (must be one of 'default', 'primary', 'success', 'info',
        'warning', or 'danger')
    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``

    Returns
    -------
    page : `~glue.markup.page`
        the formatted HTML for this block
    """
    page = markup.page()
    page.div(class_='panel panel-%s' % context, id_='block-%s' % block.key)
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
    page.h3('%s' % block.name, class_='panel-title')
    page.div.close()  # panel-heading

    # -- make body
    page.div(class_='panel-body')

    # -- range over channels in this block
    for i, channel in enumerate(block.channels):
        try:  # display channels only if they were analyzed
            channel.energy
        except AttributeError:
            continue
        page.pre('%s' % cis_link(channel.name))
        page.div(class_="container")
        # summary information
        chanstring = channel.name.replace('-', '_').replace(':', '-')
        page.div(class_='clearfix', id_='%s-%s-summary'
                                        % (block.key, chanstring))
        # arrange plots
        page.div(class_='row', style='margin-bottom: 15px; width: 97%;')
        page.div(class_='col-sm-4')
        page.p('Timeseries view: ')
        page.div(class_='btn-group btn-group-sm')
        page.add(toggle_button('timeseries_raw', channel, channel.pranges,
                               context))
        page.add(toggle_button('timeseries_highpassed', channel,
                               channel.pranges, context))
        page.add(toggle_button('timeseries_whitened', channel, channel.pranges,
                               context))
        page.div.close()  # btn-group
        page.div.close()  # col-sm-4
        page.div(class_='col-sm-4')
        page.p('Q-transform view: ')
        page.div(class_='btn-group btn-group-sm')
        page.add(toggle_button('qscan_raw', channel, channel.pranges,
                               context))
        page.add(toggle_button('qscan_whitened', channel, channel.pranges,
                               context))
        page.add(toggle_button('qscan_autoscaled', channel, channel.pranges,
                               context))
        page.div.close()  # btn-group
        page.div.close()  # col-sm-4
        page.div(class_='col-sm-4')
        page.p('Eventgram view: ')
        page.div(class_='btn-group btn-group-sm')
        page.add(toggle_button('eventgram_raw', channel, channel.pranges,
                               context))
        page.add(toggle_button('eventgram_whitened', channel, channel.pranges,
                               context))
        page.add(toggle_button('eventgram_autoscaled', channel,
                               channel.pranges, context))
        page.div.close()  # btn-group
        page.div.close()  # col-sm-4
        page.div.close()  # row
        page.div.close()  # clearfix
        page.div(class_='row')
        # summary table
        page.div(class_='col-md-3', style='margin-bottom: 20px;')
        page.p("Properties of the most significant time-frequency tile")
        page.table(class_=tableclass, style='width: 95%;')
        header = ['GPS Time', 'Frequency', 'Q Factor', 'Energy', 'SNR']
        entry = ['%.3f' % channel.t, '%.1f Hz' % channel.f,
                 '%.1f' % channel.Q, '%.1f' % channel.energy,
                 '%.1f' % channel.snr]
        page.tbody()
        for h, ent in zip(header, entry):
            page.tr()
            page.td('<b>%s</b>' % h)
            page.td(ent)
            page.tr.close()
        page.tbody.close()
        page.table.close()
        page.div.close()  # col-md-3
        # plots
        page.div(class_='col-md-9', style='margin-bottom: 20px;',
                 id_='%s-%s-plots' % (block.key, chanstring))
        page.add(scaffold_plots(channel.plots['qscan_whitened'],
                 nperrow=min(len(channel.pranges), 2)))
        page.div.close()  # col-md-9
        page.div.close()  # row
        page.div.close()  # container

    # close and return
    page.div.close()  # panel-body
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
    blocks : `list` of `OmegaChannelList`
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
    page.add(write_toc(blocks))
    page.h2('Results')
    page.p('The following blocks of channels were scanned for interesting '
           'time-frequency morphology:')
    for block in blocks:
        page.add(write_block(block, context))
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
    context : `str`, optional
        the bootstrap context class for this result, see the bootstrap
        docs for more details
    outdir : `str`, optional
        the output directory for the HTML

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
    page = markup.page()
    page.h2('On the command line')
    page.p('This page was generated with the command line call shown below.')
    page.pre(' '.join(sys.argv))
    page.h2('Configuration file')
    page.p('Omega scans are configured through INI-format files. The files '
           'used for this analysis are reproduced below in full.')
    for configfile in configfiles:
        page.pre(write_config_html(configfile))
    return page
