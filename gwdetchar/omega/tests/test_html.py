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
import sys
import shutil
import datetime
from getpass import getuser

try:  # python 3.x
    from io import StringIO
    from html.parser import HTMLParser
    from html.entities import name2codepoint
except:  # python 2.7
    from cStringIO import StringIO
    from HTMLParser import HTMLParser
    from htmlentitydefs import name2codepoint

import pytest

from .. import html
from ..._version import get_versions

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# global test objects

VERSION = get_versions()['version']
COMMIT = get_versions()['full-revisionid']

HTML_FOOTER = """<footer class="footer">
<div class="container">
<div class="row">
<div class="col-md-12">
<p>Page generated using <a style="color:#eee;" href="https://github.com/gwdetchar/gwdetchar/tree/%s" target="_blank">GW-DetChar version %s</a> by {user} at {date}</p>
</div>
</div>
</div>
</footer>""" % (COMMIT, VERSION)  # nopep8

HTML_CLOSE = """</div>
%s
</body>
</html>""" % HTML_FOOTER


# -- class for HTML diffs -----------------------------------------------------

class TestHTMLParser(HTMLParser):
    """See https://docs.python.org/3/library/html.parser.html.
    """
    def handle_starttag(self, tag, attrs):
        print("Start tag:", tag)
        attrs.sort()
        for attr in attrs:
            print("attr:", attr)

    def handle_endtag(self, tag):
        print("End tag:", tag)

    def handle_data(self, data):
        print("Data:", data)

    def handle_comment(self, data):
        print("Comment:", data)

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        print("Named entity:", c)

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        print("Numeric entity:", c)

    def handle_decl(self, data):
        print("Decl:", data)


# -- unit tests ---------------------------------------------------------------

def parse_html(html):
    parser = TestHTMLParser()
    stdout = sys.stdout
    sys.stdout = StringIO()
    parser.feed(html)
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    return output


def test_close_page(tmpdir):
    # test simple content
    target = os.path.join(str(tmpdir), 'test.html')
    date = datetime.datetime.now()
    page = html.close_page(html.markup.page(), target, date=date)
    assert parse_html(str(page)) == parse_html(
        HTML_CLOSE.format(user=getuser(), date=str(date)))
    assert os.path.isfile(target)
    with open(target, 'r') as fp:
        assert fp.read() == str(page)
    shutil.rmtree(target, ignore_errors=True)


def test_fancy_plot():
    # create a dummy FancyPlot instance
    test = html.FancyPlot('test.png')
    assert test.img is 'test.png'
    assert test.caption is 'test.png'

    # check that its properties are unchanged when the argument
    # to FancyPlot() is also a FancyPlot instance
    test = html.FancyPlot(test)
    assert test.img is 'test.png'
    assert test.caption is 'test.png'


@pytest.mark.parametrize('args, kwargs, result', [
    (('test.html', 'Test link'), {},
     '<a href="test.html" target="_blank">Test link</a>'),
    (('test.html', 'Test link'), {'class_': 'test-case'},
     '<a class="test-case" href="test.html" target="_blank">Test link</a>'),
])
def test_html_link(args, kwargs, result):
    h1 = parse_html(html.html_link(*args, **kwargs))
    h2 = parse_html(result)
    assert h1 == h2


def test_cis_link():
    h1 = parse_html(html.cis_link('X1:TEST-CHANNEL'))
    h2 = parse_html(
        '<a style="font-family: Monaco, &quot;Courier New&quot;, '
        'monospace; color: black;" href="https://cis.ligo.org/channel/byname/'
        'X1:TEST-CHANNEL" target="_blank" title="CIS entry for '
        'X1:TEST-CHANNEL">X1:TEST-CHANNEL</a>'
    )
    assert h1 == h2


def test_fancybox_img():
    img = html.FancyPlot('X1-TEST_STRAIN-test-4.png')
    out = html.fancybox_img(img)
    assert parse_html(out) == parse_html(
        '<a class="fancybox" href="X1-TEST_STRAIN-test-4.png" target="_blank" '
            'data-fancybox-group="qscan-image" id="a_X1-TEST_STRAIN_4" '
            'title="X1-TEST_STRAIN-test-4.png">\n'
        '<img class="img-responsive" alt="X1-TEST_STRAIN-test-4.png" '
            'src="X1-TEST_STRAIN-test-4.png" id="img_X1-TEST_STRAIN_4"/>\n'
        '</a>'
    )


def test_scaffold_plots():
    h1 = parse_html(html.scaffold_plots([
        html.FancyPlot('X1-TEST_STRAIN-test-4.png'),
        html.FancyPlot('X1-TEST_STRAIN-test-16.png')], nperrow=2))
    h2 = parse_html(
        '<div class="row">\n'
        '<div class="col-sm-6">\n'
        '<a class="fancybox" href="X1-TEST_STRAIN-test-4.png" target="_blank" '
            'id="a_X1-TEST_STRAIN_4" data-fancybox-group="qscan-image" '
            'title="X1-TEST_STRAIN-test-4.png">\n'
        '<img class="img-responsive" alt="X1-TEST_STRAIN-test-4.png" '
            'id="img_X1-TEST_STRAIN_4" src="X1-TEST_STRAIN-test-4.png" />\n'
        '</a>\n'
        '</div>\n'
        '<div class="col-sm-6">\n'
        '<a class="fancybox" href="X1-TEST_STRAIN-test-16.png" target="_blank"'
            ' id="a_X1-TEST_STRAIN_16" data-fancybox-group="qscan-image" '
            'title="X1-TEST_STRAIN-test-16.png">\n'
        '<img class="img-responsive" alt="X1-TEST_STRAIN-test-16.png" '
            'id="img_X1-TEST_STRAIN_16" src="X1-TEST_STRAIN-test-16.png" />\n'
        '</a>\n'
        '</div>\n'
        '</div>'
    )
    assert h1 == h2


def test_write_footer():
    date = datetime.datetime.now()
    out = html.write_footer(date=date)
    assert parse_html(str(out)) == parse_html(
        HTML_FOOTER.format(user=getuser(), date=date))
