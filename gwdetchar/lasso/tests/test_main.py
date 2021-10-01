"""Tests for gwdetchar.lasso.__main__
"""

import tempfile

import numpy as np

from gwpy.timeseries import TimeSeries

from .. import __main__ as lasso


__author__ = 'Michael Lowry <michaeljohn.lowry@ligo.org>'


# global test objects

# volatile temp file to write expected timeseries to
TEMP = tempfile.NamedTemporaryFile()
TEST_CHANNEL = 'L1:DMT-SNSW_EFFECTIVE_RANGE_MPC.mean'
TEST_START = 0
TEST_END = TEST_START+1000
TEST_ARRAY = np.linspace(TEST_START, TEST_END, num=TEST_END-TEST_START)
expected_ts = TimeSeries(TEST_ARRAY, t0=TEST_START, dt=1, channel=TEST_CHANNEL)
expected_ts.write(TEMP, format='gwf')


# # -- unit tests -------------------------------------------------------------

def test_read():
    # test reading primary TimeSeries file
    # try finally for closing temp file
    try:
        actual_ts = lasso.get_primary_ts(filepath=TEMP, channel=TEST_CHANNEL,
                                         start=TEST_START, end=TEST_END,
                                         cache=None, nproc=1)
    finally:
        TEMP.close
    assert actual_ts.t0 == expected_ts.t0
    assert actual_ts.times[-1] == expected_ts.times[-1]
    assert actual_ts.sample_rate == expected_ts.sample_rate
    assert actual_ts.dx == expected_ts.dx
    np.testing.assert_array_equal(actual_ts.value, expected_ts.value,
                                  err_msg='read in data array does not match')
