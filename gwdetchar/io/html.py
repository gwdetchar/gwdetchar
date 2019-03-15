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
from getpass import getuser
from operator import itemgetter
from shutil import copyfile
try:
    from pathlib2 import Path
except ImportError:  # python >= 3.6
    # NOTE: we do it this was around because pathlib exists for py35,
    #       but doesn't work very well
    from pathlib import Path

from six.moves import StringIO
from six.moves.urllib.parse import urlparse

from pkg_resources import resource_filename

from MarkupPy import markup

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from gwpy.time import from_gps

from ..plot import plot_segments
from .._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# -- HTML URLs ----------------------------------------------------------------

JQUERY_JS = "https://code.jquery.com/jquery-1.12.3.min.js"

BOOTSTRAP_CSS = (
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css")
BOOTSTRAP_JS = (
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js")

_FANCYBOX_CDN = "https://cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5"
FANCYBOX_CSS = "{0}/jquery.fancybox.min.css".format(_FANCYBOX_CDN)
FANCYBOX_JS = "{0}/jquery.fancybox.min.js".format(_FANCYBOX_CDN)

MOMENT_JS = (
    "https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.13.0/moment.min.js")

BOOTSTRAP_LIGO_CSS = resource_filename(
    'gwdetchar',
    '_static/bootstrap-ligo.min.css',
)
BOOTSTRAP_LIGO_JS = resource_filename(
    'gwdetchar',
    '_static/bootstrap-ligo.min.js',
)

CSS_FILES = [
    BOOTSTRAP_CSS,
    FANCYBOX_CSS,
    BOOTSTRAP_LIGO_CSS,
]
JS_FILES = [
    JQUERY_JS,
    MOMENT_JS,
    BOOTSTRAP_JS,
    FANCYBOX_JS,
    BOOTSTRAP_LIGO_JS,
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

def finalize_static_urls(static, cssfiles, jsfiles):
    """Finalise the necessary CSS and javascript files as URLS.

    The method parses the lists of files given, copying any local files into
    ``static`` as necessary to create resolvable URLs to include in the HTML
    ``<head>``.

    Parameters
    ----------
    static : `str`
        the target directory for the static files, will be created if
        necessary

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
    base = static.parent

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


def new_bootstrap_page(*args, **kwargs):
    """Create a new `~markup.page` with twitter bootstrap CSS and JS headers
    """
    # add bootstrap CSS if needed
    css = kwargs.pop('css', [])
    if BOOTSTRAP_CSS not in css:
        css.insert(0, BOOTSTRAP_CSS)
    # add jquery and bootstrap JS if needed
    script = kwargs.pop('script', [])
    for js in [BOOTSTRAP_JS, JQUERY_JS]:
        if js not in script:
            script.insert(0, js)
    # ensure nice formatting on mobile screens
    metainfo = {
        'viewport': 'width=device-width, initial-scale=1.0'}
    # create page and init
    kwargs['css'] = css
    kwargs['script'] = script
    kwargs['metainfo'] = metainfo
    page = markup.page()
    page.init(*args, **kwargs)
    return page


def write_param(param, value):
    """Format a parameter value with HTML
    """
    page = markup.page()
    page.p()
    page.strong('%s: ' % param)
    page.add(str(value))
    page.p.close()
    return page()


def render_code(code, language):
    """Render a black of code with syntax highlighting

    Parameters
    ----------
    code : `str`
        a raw block of source code

    language : `str`
        language the code is written in, e.g. `'python'`
    """
    lexer = get_lexer_by_name(language, stripall=True)
    return highlight(code, lexer, FORMATTER)


def get_command_line(language='bash'):
    """Render the command line invocation used to generate a page

    Parameters
    ----------
    language : `str`, optional
        language the code is written in, default: `'bash'`
    """
    commandline = ' '.join(sys.argv)
    return render_code(commandline, language)


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


def write_arguments(content, start, end, flag=None, section='Parameters',
                    info='This analysis used the following parameters:'):
    """Render an informative section with run parameters in HTML

    Parameters
    ----------
    content: `dict`
        a collection of parameters to list

    section: `str`
        name of the section, will appear as a header with an <h2> tag
    """
    content.insert(0, ('Start time', '{} ({})'.format(start, from_gps(start))))
    content.insert(1, ('End time', '{} ({})'.format(end, from_gps(end))))
    if flag is not None:
        content.insert(2, ('State flag', flag))
    page = markup.page()
    page.h2(section)
    page.p(info)
    for item in content:
        page.add(write_param(*item))
    page.add(write_param('Command line', ''))
    page.add(get_command_line())
    return page()


def write_flag_html(flag, span=None, id=0, parent='accordion',
                    context='warning', title=None, plotdir=None,
                    plot_func=plot_segments, **kwargs):
    """Write HTML for data quality flags
    """
    page = markup.page()
    page.div(class_='panel panel-%s' % context)
    page.div(class_='panel-heading')
    if title is None:
        title = flag.name
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


def write_footer(about=None, date=None, class_=False,
                 linkstyle='color:#000;'):
    """Write a <footer> for a bootstrap page

    Parameters
    ----------
    about : `str`, optional
        path of about page to link

    date : `datetime.datetime`, optional
        the datetime representing when this analysis was generated, defaults
        to `~datetime.datetime.now`

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the markup object containing the footer HTML
    """
    page = markup.page()
    if class_:
        page.twotags.append('footer')
        markup.element('footer', case=page.case, parent=page)(class_='footer')
    page.div(class_='container')
    # write user/time for analysis
    if date is None:
        date = datetime.datetime.now().replace(second=0, microsecond=0)
    version = get_versions()['version']
    commit = get_versions()['full-revisionid']
    url = 'https://github.com/gwdetchar/gwdetchar/tree/{}'.format(commit)
    link = markup.oneliner.a('gwdetchar version {}'.format(version), href=url,
                              target='_blank', style=linkstyle)
    page.div(class_='row')
    page.div(class_='col-md-12')
    page.p('These results were obtained using {link} by {user} at '
           '{date}.'.format(link=link, user=getuser(), date=date))
    # link to 'about'
    if about is not None:
        page.a('How was this page generated?', href=about, style=linkstyle)
    page.div.close()  # col-md-12
    page.div.close()  # row
    page.div.close()  # container
    if class_:
        markup.element('footer', case=page.case, parent=page).close()
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
    page.table(class_=class_)
    if caption is not None:
        page.caption(caption)
    page.thead()
    page.tr()
    for head in cols:
        page.th(head.title(), scope="col")
    page.tr.close()
    page.thead.close()
    page.tbody()
    for pkg in sorted(pkgs, key=itemgetter("name")):
        page.tr()
        for col in cols:
            page.td(pkg[col.lower()])
        page.tr.close()
    page.tbody.close()
    page.table.close()

    return page()
