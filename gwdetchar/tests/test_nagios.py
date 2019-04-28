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

"""Unit tests for gwdetchar.nagios
"""

import os
import json
import shutil

from .. import nagios

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# -- unit tests ---------------------------------------------------------------

def test_write_status(tmpdir):
    outdir = str(tmpdir)
    nagios.write_status(
        'This is a test success message',
        0,
        timeout=42,
        tmessage='This is a test timeout message',                       
        outdir=outdir
    )
    # test output
    filepath = os.path.join(outdir, 'nagios.json')
    with open(filepath, 'r') as fobj:
        status = json.load(fobj)
    assert isinstance(status['created_gps'], int)
    assert isinstance(status['status_intervals'], list)
    assert len(status['status_intervals']) == 2
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
