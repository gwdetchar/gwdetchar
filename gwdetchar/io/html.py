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

import os
import sys
import datetime
from getpass import getuser
from six.moves import StringIO

from MarkupPy import markup

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from ..plot import plot_segments
from .._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

JQUERY_JS = "https://code.jquery.com/jquery-1.11.2.min.js"

BOOTSTRAP_CSS = (
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css")
BOOTSTRAP_JS = (
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js")

FORMATTER = HtmlFormatter(noclasses=True)


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
        page.a(href=png, target='_blank')
        page.img(style="width: 100%;", src=png)
        page.a.close()
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
    return page
