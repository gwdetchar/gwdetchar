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

from glue import markup

from .. import version

__version__ = version.version
__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

JQUERY_JS = "//code.jquery.com/jquery-1.11.2.min.js"

BOOTSTRAP_CSS = (
    "//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css")
BOOTSTRAP_JS = (
    "//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js")


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
