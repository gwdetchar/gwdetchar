# -*- coding: utf-8 -*-
# Copyright (C) Joshua Smith (2016-)
#
# This file is part of the GW DetChar python package.
#
# gwdetchar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwdetchar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Test suite for `gwdetchar.condor`
"""

import json
import os
import tempfile

import pytest

from .. import (condor, const)

LAST_CONDOR_EPOCH = list(filter(
    condor.OBS_RUN_REGEX.match,
    list(zip(*sorted(const.EPOCH.items(), key=lambda x: x[1].start)))[0],
))[-1]


@pytest.mark.parametrize('gps, epoch', [
    (0, 'S6'),  # earlier than first run, pin to first
    (1126259462, 'O1'),  # in a run
    (2e50, LAST_CONDOR_EPOCH),  # beyond last run, pin to latest
])
def test_accounting_epoch(gps, epoch):
    assert condor.accounting_epoch(gps) == epoch


@pytest.fixture
def tagfile():
    name = tempfile.mktemp()
    with open(name, 'w') as tmp:
        json.dump({'groups': ['tag1', 'tag2', 'tag3']}, tmp)
    try:
        yield name
    finally:
        os.remove(name)


@pytest.mark.parametrize('tag, result', [
    ('tag1', True),
    ('something else', False),
])
def test_validate_accounting_tag(tagfile, tag, result):
    assert condor.validate_accounting_tag(tag, path=tagfile) == result
    if result:
        assert condor.is_valid(tag, path=tagfile) == result
    else:
        with pytest.raises(ValueError):
            condor.is_valid(tag, path=tagfile)
