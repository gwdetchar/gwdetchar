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

"""Utilties for HTML output
"""

import json
import os
import sys
import datetime
import subprocess
from io import StringIO
from pytz import reference
from getpass import getuser
from operator import itemgetter
from urllib.parse import urlparse
from collections import OrderedDict
from shutil import copyfile
try:
    from pathlib2 import Path
except ImportError:  # python >= 3.6
    # NOTE: we do it this was around because pathlib exists for py35,
    #       but doesn't work very well
    from pathlib import Path

from inspect import (getmodule, stack)
from pkg_resources import resource_filename

from MarkupPy import markup

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from gwpy.time import from_gps

from ..plot import plot_segments
from .._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credit__ = 'Alex Urban <alexander.urban@ligo.org>'

# -- navigation toggle

NAVBAR_TOGGLE = """<button class="navbar-toggle" data-toggle="collapse" type="button" data-target=".navbar-collapse">
<span class="icon-bar"></span>
<span class="icon-bar"></span>
<span class="icon-bar"></span>
</button>"""  # noqa: E501

# -- give context for ifo names

OBSERVATORY_MAP = {
    'G1': {
        'name': 'GEO',
        'context': 'default',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day')])
    },
    'H1': {
        'name': 'LIGO Hanford',
        'context': 'danger',
        'links': OrderedDict([
            ('LHO Summary Pages', 'https://ldas-jobs.ligo-wa.caltech.edu/'
                                  '~detchar/summary/day'),
            ('LHO Logbook', 'https://alog.ligo-wa.caltech.edu/aLOG')])
    },
    'I1': {
        'name': 'LIGO India',
        'context': 'success',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day')])
    },
    'K1': {
        'name': 'KAGRA',
        'context': 'warning',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day'),
            ('KAGRA Logbook', 'http://klog.icrr.u-tokyo.ac.jp/osl')])
    },
    'L1': {
        'name': 'LIGO Livingston',
        'context': 'info',
        'links': OrderedDict([
            ('LLO Summary Pages', 'https://ldas-jobs.ligo-la.caltech.edu/'
                                  '~detchar/summary/day'),
            ('LLO Logbook', 'https://alog.ligo-la.caltech.edu/aLOG')])
    },
    'V1': {
        'name': 'Virgo',
        'context': 'default',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day/'),
            ('Virgo Logbook', 'https://logbook.virgo-gw.eu/virgo')])
    },
    'Network': {
        'name': 'Multi-IFO',
        'context': 'default',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day'),
            ('LHO Logbook', 'https://alog.ligo-wa.caltech.edu/aLOG'),
            ('LLO Logbook', 'https://alog.ligo-la.caltech.edu/aLOG'),
            ('Virgo Logbook', 'https://logbook.virgo-gw.eu/virgo'),
            ('KAGRA Logbook', 'http://klog.icrr.u-tokyo.ac.jp/osl')])
    }
}

# -- HTML URLs

JQUERY_JS = "https://code.jquery.com/jquery-1.12.4.min.js"

_BOOTSTRAP_CDN = "https://stackpath.bootstrapcdn.com/bootstrap/3.4.1"
BOOTSTRAP_CSS = "{}/css/bootstrap.min.css".format(_BOOTSTRAP_CDN)
BOOTSTRAP_JS = "{}/js/bootstrap.min.js".format(_BOOTSTRAP_CDN)

_FANCYBOX_CDN = "https://cdnjs.cloudflare.com/ajax/libs/fancybox/3.5.7"
FANCYBOX_CSS = "{0}/jquery.fancybox.min.css".format(_FANCYBOX_CDN)
FANCYBOX_JS = "{0}/jquery.fancybox.min.js".format(_FANCYBOX_CDN)

GOOGLE_FONT_CSS = ("https://fonts.googleapis.com/css?"
                   "family=Roboto:400,500%7CRoboto+Mono")

FONT_AWESOME_CSS = ("https://cdnjs.cloudflare.com/ajax/libs/"
                    "font-awesome/5.10.2/css/fontawesome.min.css")
FONT_AWESOME_SOLID_CSS = ("https://cdnjs.cloudflare.com/ajax/libs/"
                          "font-awesome/5.10.2/css/solid.min.css")

BOOTSTRAP_LIGO_CSS = resource_filename(
    'gwdetchar',
    '_static/bootstrap-ligo.min.css')
BOOTSTRAP_LIGO_JS = resource_filename(
    'gwdetchar',
    '_static/bootstrap-ligo.min.js')

GWDETCHAR_CSS = resource_filename(
    'gwdetchar',
    '_static/gwdetchar.min.css')
GWDETCHAR_JS = resource_filename(
    'gwdetchar',
    '_static/gwdetchar.min.js')

CSS_FILES = [
    BOOTSTRAP_CSS,
    FANCYBOX_CSS,
    GOOGLE_FONT_CSS,
    FONT_AWESOME_CSS,
    FONT_AWESOME_SOLID_CSS,
    BOOTSTRAP_LIGO_CSS,
    GWDETCHAR_CSS]
JS_FILES = [
    JQUERY_JS,
    BOOTSTRAP_JS,
    FANCYBOX_JS,
    BOOTSTRAP_LIGO_JS,
    GWDETCHAR_JS]

FORMATTER = HtmlFormatter(noclasses=True)


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

def finalize_static_urls(static, base, cssfiles, jsfiles):
    """Finalise the necessary CSS and javascript files as URLS.

    The method parses the lists of files given, copying any local files into
    ``static`` as necessary to create resolvable URLs to include in the HTML
    ``<head>``.

    Parameters
    ----------
    static : `str`
        the target directory for the static files, will be created if
        necessary

    base : `str`
        the base directory of the website

    cssfiles : `list` of `str`
        the list of CSS files to include

    jsfiles : `list` of `str`
        the (complete) list of javascript files to include

    Returns
    -------
    cssurls : `list` of `str`
        the finalised list of CSS files

    jsurls : `list` of `str`
        the finalised list of javascript files
    """
    static = Path(static).resolve()
    base = Path(base).resolve()

    def _local_url(path):
        """Copy a filepath into the static dir if required
        """
        path = Path(path).resolve()
        # if file is already below static in the hierarchy, don't do anything
        if static in path.parents:
            return path.relative_to(base)
        # otherwise copy the file into static
        static.mkdir(parents=True, exist_ok=True)
        local = static / path.name
        copyfile(str(path), str(local))  # only need str for py<3.6
        return str(local.relative_to(base))

    # copy lists so that we can modify
    cssfiles = list(cssfiles)
    jsfiles = list(jsfiles)

    for flist in (cssfiles, jsfiles):
        for i, fn in enumerate(flist):
            url = urlparse(fn)
            if url.netloc in {"", "file"}:
                flist[i] = _local_url(fn)

    return cssfiles, jsfiles


def new_bootstrap_page(base=os.path.curdir, path=os.path.curdir, lang='en',
                       refresh=False, topbtn=True, navbar=None, **kwargs):
    """Create a new `~markup.page` with custom twitter bootstrap CSS and
    JS headers

    Parameters
    ----------
    base : `str`, optional
        relative path to the base directory, default: `.`

    path : `str`, optional
        path to directory where the page is located, default: `.`

    lang : `str`, optional
        language of the page, default: en

    refresh : `bool`, optional
        boolean switch to enable periodic page refresh, default: False

    topbtn : `bool`, optional
        boolean switch to include or exclude a floating button that scrolls
        to the top of the page, default: True

    navbar : `str`, optional
        HTML enconding of a floating navbar, will be ignored if not given,
        default: None

    Returns
    -------
    page : `~MarkupPy.markup.page`
        a populated HTML page object, which can be appended to as desired
    """
    # get kwargs with sensible defaults
    css = kwargs.pop('css', CSS_FILES)
    script = kwargs.pop('script', JS_FILES)
    # write CSS to static dir
    css, script = finalize_static_urls(
        os.path.join(path, 'static'),
        os.path.curdir,
        css,
        script,
    )
    # create page
    page = markup.page()
    page.header.append('<!DOCTYPE HTML>')
    page.html(lang=lang)
    page.head()
    if refresh:  # force-refresh if requested
        page.meta(http_equiv='refresh', content='60')
    # ensure nice formatting on most devices
    page.meta(http_equiv='Content-Type', content='text/html; charset=utf-8')
    page.meta(content='width=device-width, initial-scale=1.0', name='viewport')
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
    # open body and container
    page.body()
    if topbtn:
        glyph = markup.oneliner.i('', class_='fas fa-arrow-up')
        page.button(glyph, title='Return to top', class_='btn-float',
                    id_='top-btn', onclick='$("#top-btn").scrollView();')
    if navbar is not None:
        page.add(navbar)
    page.div(class_='container')
    return page


def navbar(links, class_='navbar navbar-fixed-top', brand=None, collapse=True):
    """Construct a navigation bar in bootstrap format

    Parameters
    ----------
    links : `list`
        list of either (text, URL) tuples or  :class:`~MarkupPy.markup.page`
        objects. Tuples will be written in ``<a>`` tags while `pages` will
        be copied directly. Both will be enclosed in a <li> element inside
        the navbar

    class_ : `str`, optional
        navbar object class, default: `'navbar navbar-fixed-top'`

    brand : `str` or `~MarkupPy.markup.page`, optional
        branding for the navigation bar, default: None

    collapse : `bool`, optional
        whether to toggle all dropdown menus, default: True

    Returns
    -------
    page : :class:`~MarkupPy.markup.page`
        navbar HTML `page` object
    """
    # page setup
    page = markup.page()
    page.twotags.extend((
        "footer",
        "header",
        "nav",
    ))
    markup.element('header', parent=page)(class_=class_)
    page.div(class_="container")

    # ---- non-collapable part (<div class="navbar-header">) ----

    page.div(class_="navbar-header")
    # add collapsed menu toggle
    if collapse:
        page.add(NAVBAR_TOGGLE)
    # add branding (generic non-collapsed content)
    if brand:
        page.add(str(brand))
    page.div.close()  # navbar-header
    if collapse:
        page.nav(class_="collapse navbar-collapse")
    else:
        page.nav()

    # ---- collapsable part (<nav>) ----

    if links:
        page.ul(class_='nav navbar-nav')
        for i, link in enumerate(links):
            if (isinstance(link, (list, tuple)) and
                    isinstance(link[1], str)):
                page.li()
                text, link = link
                page.a(text, href=link)
            elif (isinstance(link, (list, tuple)) and
                  isinstance(link[1], (list, tuple))):
                page.li(class_='dropdown')
                page.add(dropdown(*link))
            else:
                page.li()
                page.add(str(link))
            page.li.close()
        page.ul.close()

    page.nav.close()
    page.div.close()
    markup.element('header', parent=page).close()
    return page()


def dropdown(text, links, active=None, class_='dropdown-toggle'):
    """Construct a dropdown menu in bootstrap format

    Parameters
    ----------
    text : `str`
        dropdown menu header

    links : `list`
        list of (Link text, linkurl) tuples or dict of such tuples for
        grouped dropdowns

    active : `int` or `list` of `ints`, optional
        collection of links to make active, default: None

    class_ : `str`, optional
        object class of the dropdown menu, default: `'dropdown-toggle'`

    Returns
    -------
    page : :class:`~MarkupPy.markup.page`
        HTML element with the following grammar:
        .. code:: html

           <a>text</a>
           <ul>
               <li>link</li>
               <li>link</li>
           </ul>
    """
    page = markup.page()
    # dropdown header
    page.a(href='#', class_=class_, **{'data-toggle': 'dropdown'})
    page.add(text)
    page.b('', class_='caret')
    page.a.close()

    # work out columns
    ngroup = sum([isinstance(x, (tuple, list)) and len(x) and
                 isinstance(x[1], (tuple, list)) for x in links])
    if ngroup < 1:
        column = ''
    else:
        ncol = min(ngroup, 4)
        column = 'col-xs-12 col-sm-%d' % (12 // ncol)

    # dropdown elements
    if column:
        page.ul(class_='dropdown-menu dropdown-%d-col row' % ncol)
    else:
        page.ul(class_='dropdown-menu')
    for i, link in enumerate(links):
        if isinstance(active, int) and i == active:
            active_ = True
        elif isinstance(active, (list, tuple)) and i == active[0]:
            active_ = active[1]
        else:
            active_ = False
        dropdown_link(page, link, active=active_, class_=column)
    page.ul.close()
    return page()


def dropdown_link(page, link, active=False, class_=''):
    """Format links within a dropdown menu

    Parameters
    ----------
    page : `~MarkupPy.markup.page`
        a `page` object to format in-place

    link : `~MarkupPy.markup.page` or `list`
        the link(s) to format

    active : `bool`, optional
        boolean switch to enable (`True`) or disable (`False`) an active link,
        default: `False`

    class_ : `str`, optional
        object class of the link, default: `''`
    """
    if link is None:
        page.li(class_='divider')
    elif active is True:
        page.li(class_='active')
    else:
        page.li()
    if isinstance(link, (tuple, list)):
        if isinstance(link[1], (tuple, list)):
            page.ul(class_=class_ + ' list-unstyled')
            page.li(link[0], class_='dropdown-header')
            for j, link2 in enumerate(link[1]):
                dropdown_link(page, link2,
                              active=(type(active) is int and active == j))
            page.ul.close()
        else:
            page.a(link[0], href=link[1])
    elif link is not None:
        page.add(str(link))
    page.li.close()


def get_brand(ifo, name, gps, about=None):
    """Return a brand for navigation bar formatting

    Parameters
    ----------
    ifo : `str`
        interferometer prefix for color-coding, e.g. `'L1'`

    name : `str`
        name of the analysis, e.g. `'Scattering'`

    gps : `float`
        GPS second of the analysis

    about : `str`, optional
        relative path to the `about` page for this analysis, default: None

    Returns
    -------
    brand : `~MarkupPy.markup.page`
        the navbar brand `page` object

    class_ : `str`
        object class of the navbar
    """
    page = markup.page()
    page.div(ifo, class_='navbar-brand')
    page.div(name, class_='navbar-brand')
    page.div(class_='btn-group pull-right ifo-links')
    page.a(class_='navbar-brand dropdown-toggle', href='#',
           **{'data-toggle': 'dropdown'})
    page.add('Links')
    page.b('', class_='caret')
    page.a.close()
    page.ul(class_='dropdown-menu')
    if about is not None:
        page.li('Internal', class_='dropdown-header')
        page.li()
        page.a('About this page', href=about)
        page.li.close()
        page.li('', class_='divider')
    page.li('External', class_='dropdown-header')
    for name, url in OBSERVATORY_MAP[ifo]['links'].items():
        if 'Summary' in name:
            day = from_gps(gps).strftime(r"%Y%m%d")
            url = '/'.join([url, day])
        page.li()
        page.a(name, href=url, target='_blank')
        page.li.close()
    page.ul.close()
    page.div.close()  # btn-group pull-right
    class_ = 'navbar navbar-fixed-top navbar-{}'.format(ifo.lower())
    return (page(), class_)


def about_this_page(config, packagelist=True):
    """Write a blurb documenting how a page was generated, including the
    command-line arguments and configuration files used

    Parameters
    ----------
    config : `str`, `list`, optional
        the absolute path(s) to one or a number of INI files used in this
        process

    packagelist : `bool`, optional
        boolean switch to include (`True`) or exclude (`False`) a
        comprehensive list of system packages

    Returns
    -------
    page : :class:`~MarkupPy.markup.page`
        the HTML page to be inserted into the #main <div>.
    """
    page = markup.page()
    page.div(class_='row')
    page.div(class_='col-md-12')
    page.h2('On the command-line')
    page.add(get_command_line())
    # render config file(s)
    page.h2('Configuration files')
    page.p('The following INI-format configuration file(s) were passed '
           'on the comand-line and are reproduced here in full:')
    if isinstance(config, str):
        with open(config, 'r') as fobj:
            contents = fobj.read()
        page.add(render_code(contents, 'ini'))
    elif isinstance(config, list):
        page.div(class_='panel-group', id="accordion")
        for i, cpfile in enumerate(config):
            page.div(class_='panel panel-default')
            page.a(href='#file%d' % i, **{'data-toggle': 'collapse',
                                          'data-parent': '#accordion'})
            page.div(class_='panel-heading')
            page.h4(os.path.basename(cpfile), class_='panel-title')
            page.div.close()
            page.a.close()
            page.div(id_='file%d' % i, class_='panel-collapse collapse')
            page.div(class_='panel-body')
            with open(cpfile, 'r') as fobj:
                contents = fobj.read()
            page.add(render_code(contents, 'ini'))
            page.div.close()
            page.div.close()
            page.div.close()
        page.div.close()
    # render package list
    if packagelist:
        page.add(package_table())
    page.div.close()
    page.div.close()
    return page()


def render_code(code, language):
    """Render a block of code with syntax highlighting

    Parameters
    ----------
    code : `str`
        a raw block of source code

    language : `str`
        language the code is written in, e.g. `'python'`

    Returns
    -------
    code : `~MarkupPy.markup.page`
        fully rendered command-line call
    """
    lexer = get_lexer_by_name(language, stripall=True)
    return highlight(code, lexer, FORMATTER)


def get_command_line(language='bash', about=True):
    """Render the command line invocation used to generate a page

    Parameters
    ----------
    language : `str`, optional
        type of environment the code is run in, default: `'bash'`

    Returns
    -------
    page : `~MarkupPy.markup.page`
        fully rendered command-line arguments
    """
    page = markup.page()
    if about:
        page.p('This page was generated with the following command-line call:')
    if sys.argv[0].endswith('__main__.py'):
        module = getmodule(stack()[1][0]).__name__
        cmdline = '$ python -m {0} {1}'.format(module, ' '.join(sys.argv[1:]))
    else:
        script = os.path.basename(sys.argv[0])
        cmdline = ' '.join(['$', script, ' '.join(sys.argv[1:])])
    page.add(render_code(cmdline.replace(' --html-only', ''), language))
    if about:
        page.p('The install path used was <code>{}</code>.'.format(sys.prefix))
    return page()


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
        'style': "font-family: Monaco, \"Courier New\", monospace; "
                 "color: black;",
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
    page : `~MarkupPy.markup.page`
        the markup object containing fancyplot HTML
    """
    page = markup.page()
    aparams = {
        'title': img.caption,
        'class_': 'fancybox',
        'target': '_blank',
        'data-fancybox-group': 'images',
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
    if img.endswith('.svg') and os.path.isfile(img.replace('.svg', '.png')):
        imgparams['src'] = img.replace('.svg', '.png')
    else:
        imgparams['src'] = img
    imgparams.update(params)
    page.img(id_='img_%s_%s' % (channel, duration), **imgparams)
    page.a.close()
    return page()


def scaffold_plots(plots, nperrow=3):
    """Embed a `list` of images in a bootstrap scaffold

    Parameters
    ----------
    plot : `list` of `FancyPlot`
        the list of image paths to embed

    nperrow : `int`
        the number of images to place in a row (on a desktop screen)

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the markup object containing the scaffolded HTML
    """
    page = markup.page()
    x = int(12//nperrow)
    # scaffold plots
    for i, p in enumerate(plots):
        if i % nperrow == 0:
            page.div(class_='row')
        page.div(class_='col-sm-%d' % x)
        page.add(fancybox_img(p))
        page.div.close()  # col
        if i % nperrow == nperrow - 1:
            page.div.close()  # row
    if i % nperrow < nperrow-1:
        page.div.close()  # row
    return page()


def download_btn(content, label='Download summary',
                 btndiv='btn-group pull-right desktop-only',
                 btnclass='btn btn-default dropdown-toggle'):
    """Toggle download options with a Bootstrap button

    Parameters
    ----------
    content : `list` of `tuple` of `str`
        collection of `(title, link)` pairs to list

    label : `str`, optional
        text appearing inside the button, default: ``Download summary``

    id_ : `str`, optional
        unique HTML identifier for this button

    btndiv : `str`, optional
        class name of the enclosing ``<div>``,
        default: ``btn-group desktop-only``

    btnclass : `str`, optional
        class name of the Bootstrap button object,
        default: ``btn btn-default dropdown-toggle``

    Returns
    -------
    page : `~MarkupPy.markup.page`
        fully rendered download button
    """
    page = markup.page()
    page.div(class_=btndiv)
    page.button(type='button', class_=btnclass,
                **{'data-toggle': 'dropdown'})
    page.add('%s <span class="caret"></span>' % label)
    page.button.close()
    page.ul(class_='dropdown-menu', role='menu',
            **{'aria-labelledby': 'summary_table_download'})
    for item in content:
        if len(item) == 2:
            text, href = item
            download = href
        else:
            text, href, download = item
        page.li(markup.oneliner.a(text, href=href, download=download))
    page.ul.close()
    page.div.close()  # btn-group
    return page()


def parameter_table(content=[], start=None, end=None, flag=None,
                    section='Parameters', id_='parameters',
                    tableclass=('table table-condensed table-hover '
                                'table-responsive table-bordered')):
    """Render an informative section with run parameters in HTML

    Parameters
    ----------
    content: `list` of `tuple` of `str`
        collection of parameters to list

    start : `float`
        GPS start time of the analysis

    end : `float`
        GPS end time of the analysis

    flag : `str`, optional
        name of a data-quality state flag required for this analysis

    section : `str`, optional
        text to label the section header (``<h2>``), default: ``Parameters``

    id_ : `str`, optional
        unique HTML identifier for this section, default: ``parameters``

    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``, defaults to a responsive
        Bootstrap table

    Returns
    -------
    page : `~MarkupPy.markup.page`
        fully rendered table of parameters
    """
    # front-load time and flag info
    common = [
        ('Start time (UTC)', '{0} ({1})'.format(from_gps(start), start)),
        ('End time (UTC)', '{0} ({1})'.format(from_gps(end), end)),
    ]
    if flag is not None:
        common.append(('State flag', markup.oneliner.code(flag)))
    content = common + content + [
        ('System prefix', markup.oneliner.code(sys.prefix))]
    # initialize page
    page = markup.page()
    if section is not None:
        page.h2(section, id_=id_)
    page.table(class_=tableclass)
    # table body
    page.tbody()
    for row in content:
        col1, col2 = row
        page.tr()
        page.td(markup.oneliner.strong(col1))
        page.td(col2)
        page.tr.close()
    page.tbody.close()
    # close table and write command-line
    page.table.close()
    page.p(markup.oneliner.strong('Command-line:'))
    page.add(get_command_line(about=False))
    return page()


def alert(text, context='info', dismiss=True):
    """Enclose text within a bootstrap dialog box

    Parameters
    ----------
    text : `str` or `list` of `str`
        text to enclose within the box, if a `list` then each item will
        be rendered in a separate `<p>` tag

    context : `str`, optional
        Bootstrap context type, default: ``info``

    dismiss : `bool`, optional
        boolean switch to enable (`True`) or disable (`False`) a dismiss
        button, default: `True`

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the rendered dialog box object
    """
    page = markup.page()
    text = (text,) if isinstance(text, str) else text
    class_ = ('alert alert-{} alert-dismissable'.format(context) if
              dismiss else 'alert alert-{}'.format(context))
    page.div(class_=class_)
    if dismiss:  # add close button
        page.button(type="button", class_="close", **{'data-dismiss': "alert"})
        page.span('&times;', **{'aria-hidden': "true"})
        page.span('Close', class_="sr-only")
        page.button.close()
    for msg in text:
        page.p(msg)
    page.div.close()
    return page()


def table(headers, data, caption=None, separator='', id=None, **class_):
    """Write a <table> with one row of headers and many rows of data

    Parameters
    ----------
    headers : `list`
        list of column header names

    data : `list` of `lists`
        list of column data lists, for ``m`` rows and ``n`` columns, this
        should have dimensions ``m x n``

    caption : `str`, optional
        content for this table's `<caption>`

    **class_
        class attribute declarations for each tag used in the table,
        any of `table`, `thead`, `tbody`, `tr`, `th`, `td`, `caption`

    Returns
    -------
    table : `~MarkupPy.markup.page`
        a formatted HTML page object containing the `<table>`
    """
    class_.setdefault('table',
                      'table table-hover table-condensed table-responsive')
    # unwrap class declarations (so we don't get empty class attributes)
    kwargs = {}
    for tag in ['table', 'thead', 'tbody', 'tr', 'th', 'td', 'caption']:
        try:
            kwargs[tag] = {'class_': class_.pop(tag)}
        except KeyError:
            kwargs[tag] = {}
    # create table and add caption
    page = markup.page(separator=separator)
    if id is not None:
        kwargs['table']['id_'] = id
    page.table(**kwargs['table'])
    if caption:
        page.caption(caption, **kwargs['caption'])
    # write headers
    page.thead(**kwargs['thead'])
    page.tr(**kwargs['tr'])
    for th in headers:
        page.th(th, scope='col', **kwargs['th'])
    page.tr.close()
    page.thead.close()
    # write body
    page.tbody(**kwargs['tbody'])
    for row in data:
        page.tr(**kwargs['tr'])
        for td in row:
            page.td(td, **kwargs['td'])
        page.tr.close()
    page.tbody.close()
    page.table.close()
    # add export button
    if id:
        page.button(
            'Export to CSV', class_='btn btn-default btn-table',
            onclick="exportTableToCSV('{name}.csv', '{name}')".format(
                name=id))
    return page()


def write_flag_html(flag, span=None, id=0, parent='accordion',
                    context='warning', title=None, plotdir=None,
                    plot_func=plot_segments, **kwargs):
    """Write HTML for data-quality flags

    Parameters
    ----------
    flag : `~gwpy.segments.DataQualityFlag`
        the flag object to represent

    span : `~gwpy.sements.Segment`, optional
        GPS start and stop time of flag duration

    id : `int`, optional
        unique identifier for the flag, default: 0

    parent : `str`, optional
        HTML identifier of the parent object, default: ``accordion``

    context : `str`, optional
        Bootstrap context type, default: ``warning``

    title : `str`, optional
        title of the flag, defaults to `flag.name`

    plotdir : `str`, optional
        path to directory containing plots, required if plotting segments

    plot_func : `func`, optional
        function used to plot segments,
        default: `~gwdetchar.plot.plot_segments`

    **kwargs : `dict`, optional
        additional keyword arguments to `plot_func`

    Returns
    -------
    page : `~MarkupPy.markup.page`
        fully rendered HTML with a panel object for the flag
    """
    page = markup.page()
    page.div(class_='panel panel-%s' % context)
    page.div(class_='panel-heading')
    title = title or flag.name
    page.a(title, class_="panel-title", href='#flag%s' % id,
           **{'data-toggle': 'collapse', 'data-parent': '#%s' % parent})
    page.div.close()
    page.div(id_='flag%s' % id, class_='panel-collapse collapse')
    page.div(class_='panel-body')
    # render segment plot
    if plotdir is not None and plot_func is not None:
        flagr = flag.name.replace('-', '_').replace(':', '-', 1)
        png = os.path.join(
            plotdir, '%s-%d-%d.png' % (flagr, span[0], abs(span)))
        plot = plot_func(flag, span, **kwargs)
        plot.save(png)
        plot.close()
        # set up fancybox
        img = FancyPlot(
            img=png, caption='Known (small) and active (large) analysis '
                             'segments for {}'.format(title))
        page.add(fancybox_img(img))
    # write segments
    segs = StringIO()
    try:
        flag.active.write(segs, format='segwizard',
                          coltype=type(flag.active[0][0]))
    except IndexError:
        page.p("No segments were found.")
    else:
        page.pre(segs.getvalue())
    page.div.close()
    page.div.close()
    page.div.close()
    return page()


def scaffold_omega_scans(times, channel, plot_durations=[1, 4, 16],
                         scandir=os.path.curdir):
    """Preview a batch of omega scans in HTML

    Parameters
    ----------
    times : `list` of `float`
        a list of GPS times to scan

    channel : `str`
        name of the channel being scanned, e.g. ``H1:GDS-CALIB_STRAIN``

    plot_durations : `list` of `int`
        list of plot durations in seconds, default: `[1, 4, 16]`

    scandir : `str`
        path to the directory containing omega scans, default: `.`

    Returns
    -------
    page : `~MarkupPy.markup.page`
        rendered scaffold of omega scan plots
    """
    page = markup.page()
    page.div(class_='panel well panel-default')
    page.div(class_='panel-heading clearfix')
    page.h3(cis_link(channel), class_='panel-title')
    page.div.close()  # panel-heading
    page.ul(class_='list-group')
    for t in times:
        page.li(class_='list-group-item')
        page.div(class_='container')
        page.div(class_='row')
        page.div(class_='pull-right')
        page.a("[full scan]",
               href='{}/{}'.format(scandir, t),
               class_='text-dark')
        page.div.close()  # pull-right
        page.h4(t)
        page.div.close()  # row
        chanstr = channel.replace('-', '_').replace(':', '-')
        plots = [
            '{}/{}/plots/{}-qscan_whitened-{}.png'.format(
                scandir, t, chanstr, dur) for dur in plot_durations]
        page.add(scaffold_plots(
            [FancyPlot(plot) for plot in plots],
            nperrow=3))
        page.div.close()  # container
        page.li.close()  # list-group-item
    page.ul.close()  # list-group
    page.div.close()  # panel
    return page()


def write_footer(about=None, link=None, issues=None, external=None):
    """Write a <footer> for a bootstrap page

    Parameters
    ----------
    about : `str`, optional
        path of about page to link

    link : `None` or `tuple`, optional
        tuple of package name, HTML link to source code, and host name
        (e.g. GitHub)

    issues : `str`, optional
        HTML link to issue report page

    external : `str`, optional
        additional footer link to an external page

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the markup object containing the footer HTML
    """
    page = markup.page()
    page.twotags.append('footer')
    markup.element('footer', case=page.case, parent=page)(class_='footer')
    page.div(class_='container')
    if link is None:
        version = get_versions()['version']
        commit = get_versions()['full-revisionid']
        package = 'gwdetchar-%s' % version
        source = 'https://github.com/gwdetchar/gwdetchar/tree/%s' % commit
        host = 'GitHub'
    elif isinstance(link, (tuple, list)):
        package, source, host = link
    else:
        raise ValueError("'link' argument must be either None or a tuple of "
                         "package name, URL, and host name")
    # format various links
    page.div(class_='row')
    page.div(class_='col-sm-3 icon-bar')
    page.a(markup.oneliner.i('', class_='fas fa-code'), href=source,
           title='View {0} on {1}'.format(package, host), target='_blank')
    page.a(markup.oneliner.i('', class_='fas fa-ticket-alt'),
           href=issues or 'https://github.com/gwdetchar/gwdetchar/issues',
           title='Open an issue ticket', target='_blank')
    if about is not None:
        page.a(markup.oneliner.i('', class_='fas fa-info-circle'),
               href=about, title='How was this page generated?')
    if external is not None:
        page.a(markup.oneliner.i('', class_='fas fa-external-link-alt'),
               href=external, title="View this page's external source")
    page.a(markup.oneliner.i('', class_='fas fa-heartbeat'),
           href='https://attackofthecute.com/random.php',
           title='Take a break from science', target='_blank')
    page.div.close()  # col-sm-3 icon-bar
    # print timestamp
    page.div(class_='col-sm-6')
    now = datetime.datetime.now()
    tz = reference.LocalTimezone().tzname(now)
    date = now.strftime('%H:%M {} on %d %B %Y'.format(tz))
    page.p('Created by {0} at {1}'.format(getuser(), date))
    page.div.close()  # col-sm-6
    page.div.close()  # row
    page.div.close()  # container
    markup.element('footer', case=page.case, parent=page).close()
    return page()


def close_page(page, target, **kwargs):
    """Close an HTML document with markup then write to disk

    This method writes the closing markup to complement the opening
    written by `init_page`, something like:

    .. code:: html

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
    """
    page.div.close()  # container
    page.add(write_footer(**kwargs))
    if not page._full:
        page.body.close()
        page.html.close()
    with open(target, 'w') as f:
        f.write(page())
    return page()


def package_list():
    """Get the list of packages installed alongside this one

    Returns a `list` of `dict`
    """
    prefix = sys.prefix
    if (Path(prefix) / "conda-meta").is_dir():
        raw = subprocess.check_output(
            ["conda", "list",
             "--prefix", prefix,
             "--json"],
        )
    else:
        raw = subprocess.check_output(
            [sys.executable,
             "-m", "pip",
             "list", "installed",
             "--format", "json"],
        )
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    return json.loads(raw)


def package_table(
        h2="Environment",
        class_="table table-hover table-condensed table-responsive",
        caption="Table of packages installed in the production environment",
        id_="package-table",
):
    """Write a table listing packages installed in the current environment

    Parameters
    ----------
    h2 : `str`, `None`, optional
        the header for the HTML section

    caption : `str`, `None`, optional
        the `<caption>` for the package table

    Returns
    -------
    html : `str`
        an HTML table
    """
    # get package list and inspect columns
    pkgs = package_list()
    if "build_string" in pkgs[0]:  # conda list
        cols = ("name", "version", "channel", "build_string")
    else:  # pip list installed
        cols = ("name", "version")
    # create page and write <table>
    page = markup.page(separator="")
    if h2 is not None:
        page.h2(h2)
    headers = [head.title() for head in cols]
    data = [[pkg[col.lower()] for col in cols]
            for pkg in sorted(pkgs, key=itemgetter("name"))]
    page.add(table(headers, data, caption=caption, id=id_, table=class_))
    return page()
