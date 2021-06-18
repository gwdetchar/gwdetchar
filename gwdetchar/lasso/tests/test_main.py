"""Tests for gwdetchar.lasso.__main__
"""

from .. import __main__ as lasso
import ....io.datafind as datafind

from numpy import testing as nptest

import tempfile

from gwpy.timeseries import TimeSeries

__author__ = 'Michael Lowry <michaeljohn.lowry@ligo.org>'

 
# global test objects

# volatile temp file to write expected timeseries to
temp = tempfile.NamedTemporaryFile()
test_channel = 'L1:DMT-SNSW_EFFECTIVE_RANGE_MPC.mean'
test_frametype = 'SenseMonitor_CAL_L1_M'
test_start = 1264983618
test_end = test_start+7200
expected_ts = datafind.get_data(test_channel, test_start, test_end, frametype=test_frametype)
expected_ts.write(temp, format='gwf')


# # -- unit tests ---------------------------------------------------------------
        
def test_read():
    print('Testing primary channel file read...')
    # try finally for closing temp file
    try:
        actual_ts = lasso.get_primary_ts(filepath=temp, channel=test_channel, start=test_start, end=test_end, frametype=test_frametype, cache=None, nproc=1)
    finally:
        temp.close
    assert actual_ts.t0 == expected_ts.t0
    assert actual_ts.times[-1] == expected_ts.times[-1]
    assert actual_ts.sample_rate == expected_ts.sample_rate
    assert actual_ts.dx == expected_ts.dx
    nptest.assert_array_equal(actual_ts.value, expected_ts.value, err_msg='read in data array does not match')

def test_get():
    print('Testing primary channel query...')
    actual_get_ts = lasso.get_primary_ts(channel='L1:DMT-SNSW_EFFECTIVE_RANGE_MPC.mean', start=test_start, end=test_end, frametype=test_frametype)
    assert actual_get_ts.t0 == expected_ts.t0
    assert actual_get_ts.times[-1] == expected_ts.times[-1]
    assert actual_get_ts.sample_rate == expected_ts.sample_rate
    assert actual_get_ts.dx == expected_ts.dx
    nptest.assert_array_equal(actual_get_ts.value, expected_ts.value, err_msg='fetched data array does not match')
