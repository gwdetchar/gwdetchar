"""Tests for gwdetchar.lasso.__main__
"""

# relative import - change before full merge
# from .. import __main__ as lasso
import gwdetchar.lasso.__main__ as lasso

import numpy as np
from numpy import testing as nptest

import tempfile

from gwpy.timeseries import TimeSeries

__author__ = 'Michael Lowry <michaeljohn.lowry@ligo.org>'

 
# global test objects

temp = tempfile.NamedTemporaryFile()
test_channel = 'Z1:Test_Range'
test_start = 1264983618
test_end = test_start+7200
expected_ts_in = np.random.random(120)
expected_ts = TimeSeries(expected_ts_in, t0=test_start, unit='Mpc', sample_rate=1/60, channel=test_channel)
expected_ts.write(temp, format='gwf')


# # -- unit tests ---------------------------------------------------------------
        
def test_read():
    print('Testing primary channel file read...')
    try:
        actual_ts = lasso.get_primary_ts(filepath=temp, channel=test_channel, start=test_start, end=test_end, cache=None, nproc=1)
        actual_ts_bp = lasso.get_primary_ts(filepath=temp, channel=test_channel, start=test_start, end=test_end, cache=None, nproc=1, band_pass=True)
    finally:
        temp.close
    assert actual_ts.t0 == expected_ts.t0
    assert actual_ts.times[-1] == expected_ts.times[-1]
    nptest.assert_array_equal(actual_ts.value, expected_ts_in, err_msg='read in data array does not match')

def test_get():
    print('Testing primary channel query...')
    actual_get_ts = lasso.get_primary_ts(channel='L1:DMT-SNSW_EFFECTIVE_RANGE_MPC.mean', start=test_start, end=test_end, frametype='SenseMonitor_CAL_L1_M')
    actual_get_ts = lasso.get_primary_ts(channel='L1:DMT-SNSW_EFFECTIVE_RANGE_MPC.mean', start=test_start, end=test_end, frametype='SenseMonitor_CAL_L1_M',
                                         band_pass=True)

