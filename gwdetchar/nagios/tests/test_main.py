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

"""Tests for the `gwdetchar.nagios` command-line interface
"""

import json
import os
import shutil

from random import randrange
from numpy.testing import assert_equal

from .. import __main__ as nagios_cli

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

# -- command-line flags

STATUS = randrange(4)
MESSAGE = 'This is a test message'
TIMEOUT = 3600


# -- cli tests ----------------------------------------------------------------

def test_main(tmpdir, caplog):
    outdir = str(tmpdir)
    outfile = os.path.join(outdir, "test.json")
    # test the status generator
    nagios_cli.main([
        str(STATUS),
        MESSAGE,
        '--timeout', str(TIMEOUT),
        '--output-file', outfile,
    ])
    assert 'Status written to {}'.format(outfile) in caplog.text
    assert os.path.isfile(outfile)
    # test output
    with open(outfile, 'r') as fobj:
        status = json.load(fobj)
    assert isinstance(status['created_gps'], int)
    assert isinstance(status['status_intervals'], list)
    assert_equal(
        status['status_intervals'][0],
        {'start_sec': 0,
         'txt_status': MESSAGE,
         'num_status': STATUS},
    )
    assert_equal(
        status['status_intervals'][1],
        {'start_sec': TIMEOUT,
         'txt_status': 'Process timed out',
         'num_status': 3},
    )
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
