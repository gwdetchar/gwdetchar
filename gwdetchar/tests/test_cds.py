# coding=utf-8
# Copyright (C) Duncan Macleod (2018)
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

"""Tests of :mod:`gwdetchar.cds`
"""

import pytest

from io import BytesIO
from unittest import mock

from .. import cds

RTDCUID_CONTENT = """
<div class="listing">
  <code>1 x1model1</code>
  <code>2 x2model2</code>
  <code>nonint x2model3</code>
  <code>3 x3model3 test</code>
</div>
"""

ADCLIST_CONTENT = """
<div class="listing">
  <code>0 0 A X</code>
  <code>0 1 B X</code>
  <code>1 0 C X </code>
  <code>A B C D</code>
  <code>1	1	D	X</code>
</div>
"""


def mock_request(output):
    if isinstance(output, str):
        output = output.encode('utf-8')
    return mock.patch('gwdetchar.cds.request.urlopen',
                      return_value=BytesIO(output))


@mock_request(RTDCUID_CONTENT)
def test_get_dcuid_map(_):
    dcuidmap = cds.get_dcuid_map('X1')
    assert dcuidmap == {
        1: 'x1model1',
        2: 'x2model2',
    }


@mock_request(ADCLIST_CONTENT)
def test_get_adclist(_):
    adclist = cds.get_adclist('X1', 'x1model1')
    assert adclist == {
        (0, 0): 'A',
        (0, 1): 'B',
        (1, 0): 'C',
        (1, 1): 'D',
    }


@mock_request(RTDCUID_CONTENT)
def test_model_name_from_dcuid(mockr):
    cds.DCUID_MAP = {}
    assert cds.model_name_from_dcuid('X1', 1) == 'x1model1'
    assert cds.model_name_from_dcuid('X1', 2) == 'x2model2'
    assert mockr.call_count == 1
    with pytest.raises(KeyError):
        assert cds.model_name_from_dcuid('X1', 9) == 1


@mock_request(RTDCUID_CONTENT)
def test_dcuid_from_model_name(mockr):
    cds.DCUID_MAP = {}
    assert cds.dcuid_from_model_name('X1', 'x1model1') == 1
    assert cds.dcuid_from_model_name('X1', 'x2model2') == 2
    assert mockr.call_count == 1
    with pytest.raises(KeyError):
        assert cds.dcuid_from_model_name('X1', 'x1model9') == 1


@mock_request(ADCLIST_CONTENT)
def test_get_adc_channel(mockr):
    cds.ADC_MAP = {}
    assert cds.get_adc_channel('X1', 'x1model1', 0, 0) == 'A'
    assert cds.get_adc_channel('X1', 'x1model1', 0, 1) == 'B'
    assert mockr.call_count == 1
    with pytest.raises(KeyError):
        assert cds.get_adc_channel('X1', 'x1model1', 9, 9)


@mock_request(ADCLIST_CONTENT)
@mock.patch(
    'gwdetchar.cds.model_name_from_dcuid',
    return_value='x1model1',
)
def test_get_real_channel(mockr, mockadc):
    assert cds.get_real_channel('X1:TEST-1_ADC_OVERFLOW_ACC_0_0') == 'A'
    assert cds.get_real_channel('X1:TEST-1_ADC_OVERFLOW_ACC_0_1') == 'B'
    assert mockr.call_count == 2
    with pytest.raises(ValueError):
        assert cds.get_real_channel('X1:TEST-1_TEST_OVERFLOW_ACC_0_0')
