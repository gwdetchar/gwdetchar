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

from six.moves import StringIO

from glue import markup

from ..plot import plot_segments

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

JQUERY_JS = "https://code.jquery.com/jquery-1.11.2.min.js"

BOOTSTRAP_CSS = (
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css")
BOOTSTRAP_JS = (
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js")


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
    # create page and init
    kwargs['css'] = css
    kwargs['script'] = script
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


def write_flag_html(flag, span=None, id=0, parent='accordion',
                    context='warning', title=None, plotdir=None,
                    plot_func=plot_segments):
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
    segs = StringIO()
    try:
        flag.active.write(segs, format='segwizard',
                          coltype=type(flag.active[0][0]))
    except IndexError:
        page.p("No segments were found.")
    else:
        page.pre(segs.getvalue())
    page.div.close()
    if plotdir is not None and plot_func is not None:
        flagr = flag.name.replace('-', '_').replace(':', '-', 1)
        png = os.path.join(
            plotdir, '%s-%d-%d.png' % (flagr, span[0], abs(span)))
        plot = plot_func(flag, span)
        plot.save(png)
        plot.close()
        page.a(href=png, target='_blank')
        page.img(style="width: 100%;", src=png)
        page.a.close()
    page.div.close()
    page.div.close()
    return page
