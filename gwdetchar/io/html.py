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

import datetime
import json
import os
import subprocess
import sys

from collections import OrderedDict
from getpass import getuser
from io import StringIO
from operator import itemgetter
from pathlib import Path
from pytz import reference
from shutil import copyfile
from urllib.parse import urlparse

from MarkupPy import markup

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from gwpy.time import from_gps

from ..plot import plot_segments
from .._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credit__ = 'Alex Urban <alexander.urban@ligo.org>'

# -- give context for ifo names

OBSERVATORY_MAP = {
    'G1': {
        'name': 'GEO',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day')])
    },
    'H1': {
        'name': 'LIGO Hanford',
        'links': OrderedDict([
            ('LHO Summary Pages', 'https://ldas-jobs.ligo-wa.caltech.edu/'
                                  '~detchar/summary/day'),
            ('LHO Logbook', 'https://alog.ligo-wa.caltech.edu/aLOG')])
    },
    'I1': {
        'name': 'LIGO India',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day')])
    },
    'K1': {
        'name': 'KAGRA',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day'),
            ('KAGRA Logbook', 'http://klog.icrr.u-tokyo.ac.jp/osl')])
    },
    'L1': {
        'name': 'LIGO Livingston',
        'links': OrderedDict([
            ('LLO Summary Pages', 'https://ldas-jobs.ligo-la.caltech.edu/'
                                  '~detchar/summary/day'),
            ('LLO Logbook', 'https://alog.ligo-la.caltech.edu/aLOG')])
    },
    'V1': {
        'name': 'Virgo',
        'links': OrderedDict([
            ('Network Summary Pages', 'https://ldas-jobs.ligo.caltech.edu/'
                                      '~detchar/summary/day/'),
            ('Virgo Logbook', 'https://logbook.virgo-gw.eu/virgo')])
    },
    'Network': {
        'name': 'Multi-IFO',
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

FONT_AWESOME_CSS = ('https://cdnjs.cloudflare.com/ajax/libs/'
                    'font-awesome/5.15.1/css/fontawesome.min.css')
FONT_AWESOME_SOLID_CSS = ('https://cdnjs.cloudflare.com/ajax/libs/'
                          'font-awesome/5.15.1/css/solid.min.css')

JQUERY_JS = 'https://code.jquery.com/jquery-3.5.1.min.js'
JQUERY_LAZY_JS = ('https://cdnjs.cloudflare.com/ajax/libs/jquery.lazy/'
                  '1.7.11/jquery.lazy.min.js')
BOOTSTRAP_JS = ('https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/'
                'dist/js/bootstrap.bundle.min.js')
FANCYBOX_JS = ('https://cdnjs.cloudflare.com/ajax/libs/'
               'fancybox/3.5.7/jquery.fancybox.min.js')

GWBOOTSTRAP_CSS = ('https://cdn.jsdelivr.net/npm/gwbootstrap@1.3.2/'
                   'lib/gwbootstrap.min.css')
GWBOOTSTRAP_JS = ('https://cdn.jsdelivr.net/npm/gwbootstrap@1.3.2/'
                  'lib/gwbootstrap.min.js')

CSS_FILES = [
    FONT_AWESOME_CSS,
    FONT_AWESOME_SOLID_CSS,
    GWBOOTSTRAP_CSS,
]

JS_FILES = [
    JQUERY_JS,
    JQUERY_LAZY_JS,
    BOOTSTRAP_JS,
    FANCYBOX_JS,
    GWBOOTSTRAP_JS,
]

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

def _get_card_header(context):
    """Return the correct bootstrap-4 card-header class for the given context
    """
    if context == 'light':
        return 'card-header bg-light'
    else:
        return 'card-header text-white bg-%s' % context


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
        page.link(href=f, rel='stylesheet', media='all')
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
        page.button(glyph, title='Return to top',
                    class_='btn-float shadow', id_='top-btn')
    if navbar is not None:
        page.add(navbar)
    page.div(class_='container')
    return page


def navbar(links, class_='navbar navbar-expand-md fixed-top shadow-sm',
           brand=None, collapse=True):
    """Construct a navigation bar in bootstrap format

    Parameters
    ----------
    links : `list`
        list of either (text, URL) tuples or  :class:`~MarkupPy.markup.page`
        objects. Tuples will be written in ``<a>`` tags while `pages` will
        be copied directly. Both will be enclosed in a <li> element inside
        the navbar

    class_ : `str`, optional
        navbar object class, default: `'navbar navbar-expand-md fixed-top'`

    brand : `str`, `~MarkupPy.markup.page`, or `list`, optional
        branding for the navigation bar, default: None

    collapse : `bool`, optional
        whether to toggle all dropdown menus, default: True

    Returns
    -------
    page : :class:`~MarkupPy.markup.page`
        navbar HTML `page` object
    """
    if isinstance(brand, (tuple, list)):
        brand, help_ = brand
    else:
        help_ = None

    # page setup
    page = markup.page()
    page.twotags.append('nav')
    page.nav(class_=class_)
    page.div(class_='container-fluid')

    # add branding (generic non-collapsed content)
    if brand is not None:
        page.add(str(brand))

    # begin navbar proper
    if collapse:
        page.button(
            class_='navbar-toggler navbar-toggler-right', type_='button',
            **{'data-toggle': 'collapse', 'data-target': '.navbar-collapse'})
        page.span('', class_='navbar-toggler-icon')
        page.button.close()
        page.div(class_='collapse navbar-collapse justify-content-between')
    else:
        page.div()

    # ---- collapsable part (<div>) ----

    if links:
        page.ul(class_='nav navbar-nav mr-auto')
        for i, link in enumerate(links):
            if (isinstance(link, (list, tuple)) and
                    isinstance(link[1], str)):
                text, link = link
                page.li(class_='nav-item')
                page.a(text, href=link, class_='nav-link')
            elif (isinstance(link, (list, tuple)) and
                  isinstance(link[1], (list, tuple))):
                page.li(class_='nav-item dropdown')
                page.add(dropdown(*link))
            elif isinstance(link, str) and not link.startswith('<'):
                page.li(class_='nav-item navbar-text')
                page.add(link)
            else:
                page.li(class_='nav-item')
                page.add(str(link))
            page.li.close()
        page.ul.close()  # nav navbar-nav mr-auto

        if help_ is not None:
            page.add(str(help_))

    page.div.close()  # collapse navbar-collapse
    page.div.close()  # container-fluid
    page.nav.close()
    return page()


def dropdown(text, links, active=None, class_='nav-link dropdown-toggle'):
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
    def has_columns(items_):
        return (isinstance(items_, (tuple, list)) and len(items_)
                and isinstance(items_[1], (tuple, list)))

    def has_open_row(page_):
        tags = page_.content
        divs = [t for t in tags if ('<div' in t)]
        cldivs = [t for t in tags if ('</div' in t)]
        return len(cldivs) != len(divs) - 1

    page = markup.page()
    page.a(text, href='#', class_=class_, role='button',
           **{'data-toggle': 'dropdown'})

    # work out columns
    ngroup = sum([has_columns(x) for x in links])
    ncol = min(ngroup, 4) or 1
    page.div(class_='dropdown-menu dropdown-%d-col shadow' % ncol)

    # dropdown elements
    for i, link in enumerate(links):
        # handle active links
        if isinstance(active, int) and i == active:
            active_ = True
        elif isinstance(active, (list, tuple)) and i == active[0]:
            active_ = active[1]
        else:
            active_ = False
        # handle multi-column
        if has_columns(link):
            if not has_open_row(page):
                page.div(class_='row')
            dropdown_link(page, link, active=active_,
                          class_='col-sm-12 col-md-%d' % (12 // ncol))
        else:
            dropdown_link(page, link, active=active_)

    # close and return
    if has_open_row(page):
        page.div.close()  # row
    page.div.close()  # dropdown-menu
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
    if link in [None, '']:
        page.div('', class_='dropdown-divider')
    elif isinstance(link, (tuple, list)):
        if isinstance(link[1], (tuple, list)):
            page.div(class_=class_)
            page.h6(link[0], class_='dropdown-header')
            for j, link2 in enumerate(link[1]):
                dropdown_link(page, link2,
                              active=(type(active) is int and active == j))
            page.div.close()
        else:
            page.a(link[0], href=link[1],
                   class_=('dropdown-item active' if active is True
                           else 'dropdown-item'))
    elif link is not None:
        page.add(str(link))


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
    # navbar brand
    brand = markup.oneliner.div(
        ' '.join([ifo, name]),
        class_='navbar-brand border border-white rounded',
    )
    # IFO links
    page = markup.page()
    page.ul(class_='nav navbar-nav')
    page.li(class_='nav-item dropdown')
    page.a('Links', class_='nav-link dropdown-toggle',
           href='#', role='button', **{'data-toggle': 'dropdown'})
    page.div(class_='dropdown-menu dropdown-menu-right shadow')
    if about is not None:
        page.h6('Internal', class_='dropdown-header')
        page.a('About this page', href=about, class_='dropdown-item')
        page.div('', class_='dropdown-divider')
    page.h6('External', class_='dropdown-header')
    for name, url in OBSERVATORY_MAP[ifo]['links'].items():
        if 'Summary' in name:
            day = from_gps(gps).strftime(r"%Y%m%d")
            url = '/'.join([url, day])
        page.a(name, href=url, class_='dropdown-item', target='_blank')
    page.div.close()  # dropdown-menu
    page.li.close()  # nav-link dropdown-toggle
    page.ul.close()  # nav navbar-nav
    class_ = ('navbar fixed-top navbar-expand-md navbar-{} '
              'shadow-sm').format(ifo.lower())
    return ((brand, page()), class_)


def about_this_page(config, packagelist=True, prog=None):
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

    prog : `str`, optional
        name of the program which produced this page, defaults to
        the script run on the command-line

    Returns
    -------
    page : :class:`~MarkupPy.markup.page`
        the HTML page to be inserted into the #main <div>.
    """
    page = markup.page()
    page.div(class_='row')
    page.div(class_='col-md-12')
    page.h2('On the command-line')
    page.add(get_command_line(prog=prog))
    # render config file(s)
    page.h2('Configuration files')
    page.p('The following INI-format configuration file(s) were passed '
           'on the comand-line and are reproduced here in full:')
    if isinstance(config, str):
        with open(config, 'r') as fobj:
            contents = fobj.read()
        page.add(render_code(contents, 'ini'))
    elif isinstance(config, list):
        page.div(id_='accordion')
        for i, cpfile in enumerate(config):
            page.div(class_='card mb-1 shadow-sm')
            page.div(class_='card-header')
            page.a(
                os.path.basename(cpfile),
                class_='collapsed card-link cis-link',
                href='#file%d' % i,
                **{'data-toggle': 'collapse'}
            )
            page.div.close()  # card-header
            page.div(id_='file%d' % i, class_='collapse',
                     **{'data-parent': '#accordion'})
            page.div(class_='card-body')
            with open(cpfile, 'r') as fobj:
                contents = fobj.read()
            page.add(render_code(contents, 'ini'))
            page.div.close()  # card-body
            page.div.close()  # collapse
            page.div.close()  # card
        page.div.close()  # accordion
    # render package list
    if packagelist:
        page.add(package_table())
    page.div.close()  # col-md-12
    page.div.close()  # row
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


def get_command_line(language='bash', about=True, prog=None):
    """Render the command-line invocation used to generate a page

    Parameters
    ----------
    language : `str`, optional
        type of environment the code is run in, default: `'bash'`

    about : `bool`, optional
        whether this markup is for an 'about' page, default: `True`

    prog : `str`, optional
        name of the program which produced this page, defaults to
        the script run on the command-line

    Returns
    -------
    page : `~MarkupPy.markup.page`
        fully rendered command-line arguments
    """
    prog = prog or os.path.basename(sys.argv[0])
    page = markup.page()
    if about:
        page.p('This page was generated with the following command-line call:')
    args = ' '.join(sys.argv[1:])
    cmdline = ' '.join(['$', prog, args])
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
        'class_': 'cis-link',
    }
    kwargs.update(params)
    return html_link("https://cis.ligo.org/channel/byname/%s" % channel,
                     channel, **kwargs)


def fancybox_img(img, linkparams=dict(), lazy=False, **params):
    """Return the markup to embed an <img> in HTML

    Parameters
    ----------
    img : `FancyPlot`
        a `FancyPlot` object containing the path of the image to embed
        and its caption to be displayed

    linkparams : `dict`, optional
        the HTML attributes for the ``<a>`` tag

    lazy : `bool`, optional
        whether to lazy-load the image, default: False

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
        'data-caption': img.caption,
        'data-fancybox': 'gallery',
        'data-fancybox-group': 'images',
    }
    aparams.update(linkparams)
    img = str(img)
    substrings = os.path.basename(img).split('-')
    channel = '%s-%s' % tuple(substrings[:2])
    duration = substrings[-1].split('.')[0]
    page.a(href=img, id_='a_%s_%s' % (channel, duration), **aparams)
    src_attr = lazy and 'data-src' or 'src'
    imgparams = {
        'alt': os.path.basename(img),
        'class_': lazy and 'img-fluid w-100 lazy' or 'img-fluid w-100',
        src_attr: img.replace('.svg', '.png'),
    }
    imgparams.update(params)
    page.img(id_='img_%s_%s' % (channel, duration), **imgparams)
    page.a.close()
    return page()


def scaffold_plots(plots, nperrow=3, lazy=True):
    """Embed a `list` of images in a bootstrap scaffold

    Parameters
    ----------
    plot : `list` of `FancyPlot`
        the list of image paths to embed

    nperrow : `int`
        the number of images to place in a row (on a desktop screen)

    lazy : `bool`, optional
        whether to lazy-load images, default: True

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
            page.div(class_='row scaffold')
        page.div(class_='col-sm-%d' % x)
        page.add(fancybox_img(p, lazy=lazy))
        page.div.close()  # col
        if i % nperrow == nperrow - 1:
            page.div.close()  # row
    if i % nperrow < nperrow-1:
        page.div.close()  # row
    return page()


def download_btn(content, label='Download summary',
                 btndiv='dropdown float-right d-none d-lg-block',
                 btnclass='btn btn-outline-secondary dropdown-toggle'):
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
        default: ``dropdown float-right d-none d-lg-block``

    btnclass : `str`, optional
        class name of the Bootstrap button object,
        default: ``btn btn-secondary dropdown-toggle``

    Returns
    -------
    page : `~MarkupPy.markup.page`
        fully rendered download button
    """
    page = markup.page()
    page.div(class_=btndiv)
    page.button(label, type='button', class_=btnclass,
                **{'data-toggle': 'dropdown',
                   'aria-expanded': 'false',
                   'aria-haspopup': 'true'})
    page.div(class_='dropdown-menu dropdown-menu-right shadow')
    for item in content:
        if len(item) == 2:
            text, href = item
            download = href
        else:
            text, href, download = item
        page.a(text, href=href, download=download,
               class_='dropdown-item')
    page.div.close()  # dropdown-menu
    page.div.close()  # btndiv
    return page()


def parameter_table(content=[], start=None, end=None, flag=None,
                    id_='parameters', tableclass='table table-sm table-hover'):
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
    page.table(class_=tableclass)
    # table body
    page.tbody()
    for row in content:
        col1, col2 = row
        page.tr()
        page.th(col1, scope='row')
        page.td(col2)
        page.tr.close()
    page.tbody.close()
    # close table and write command-line
    page.table.close()
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
    class_ = ('alert alert-%s alert-dismissible fade show text-justify '
              'shadow-sm' % context if dismiss else
              'alert alert-%s text-justify shadow-sm' % context)
    page.div(class_=class_)
    if dismiss:  # add close button
        page.button(type_="button", class_="close",
                    **{'data-dismiss': 'alert', 'aria-label': 'Close'})
        page.span('&times;', **{'aria-hidden': "true"})
        page.button.close()
    if isinstance(text, (list, tuple)):
        for msg in text:
            page.p(str(msg))
    else:
        page.add(str(text))
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
    class_.setdefault('table', 'table table-sm table-hover')
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
            'Export to CSV', class_='btn btn-outline-secondary btn-table mt-2',
            **{'data-table-id': id, 'data-filename': '%s.csv' % id})
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
        fully rendered HTML with a card object for the flag
    """
    page = markup.page()
    page.div(class_='card border-%s mb-1 shadow-sm' % context)
    page.div(class_=_get_card_header(context))
    title = title or flag.name
    page.a(title, class_='collapsed card-link cis-link', href='#flag%s' % id,
           **{'data-toggle': 'collapse'})
    page.div.close()  # card-header
    page.div(id_='flag%s' % id, class_='collapse',
             **{'data-parent': '#' + parent})
    page.div(class_='card-body')
    # render segment plot
    if (plotdir is not None) and (plot_func is not None):
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
        page.add(scaffold_plots([img], nperrow=1, lazy=False))
    # write segments
    segs = StringIO()
    try:
        flag.active.write(segs, format='segwizard',
                          coltype=type(flag.active[0][0]))
    except IndexError:
        page.p('No segments were found.')
    else:
        page.pre(segs.getvalue())
    page.div.close()  # card-body
    page.div.close()  # collapse
    page.div.close()  # card
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
    ifo = channel[:2].lower()
    page = markup.page()
    page.div(class_='card card-%s' % ifo)
    page.div(class_='card-header pb-0')
    page.h5(cis_link(channel), class_='card-title')
    page.div.close()  # card-header
    page.div(class_='card-body')
    page.ul(class_='list-group')
    for t in times:
        page.li(class_='list-group-item')
        page.div(class_='container')
        page.div(class_='row')
        page.h6()
        page.a(t, href='{0}/{1}'.format(scandir, t), class_='text-dark')
        page.h6.close()
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
    page.div.close()  # card-body
    page.div.close()  # card
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
           href='https://apod.nasa.gov/apod/astropix.html',
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
        class_='table table-sm table-hover table-responsive',
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
        page.h2(h2, class_='mt-4')
    headers = [head.title() for head in cols]
    data = [[pkg[col.lower()] for col in cols]
            for pkg in sorted(pkgs, key=itemgetter("name"))]
    page.add(table(headers, data, caption=caption, id=id_, table=class_))
    return page()
