"""Tests for gwdetchar.lasso.__main__
"""
import pytest

import numpy as np

from gwpy.timeseries import TimeSeries

from .. import __main__ as lasso


__author__ = "Michael Lowry <michaeljohn.lowry@ligo.org>"


# global test objects

TEST_CHANNEL = "test_channel"
TEST_START = 0
TEST_END = TEST_START+1000


# # -- pytest fixtures -------------------------------------------------------
@pytest.fixture
def expected_ts():
    # construct random data to read
    data = np.linspace(TEST_START, TEST_END, num=TEST_END-TEST_START)
    return TimeSeries(data, t0=TEST_START, dt=1, channel=TEST_CHANNEL,
                      name=TEST_CHANNEL)


@pytest.fixture
def expected_ts_file(expected_ts, tmp_path):
    # write data to file and return that file
    outfile = tmp_path / "data.gwf"
    expected_ts.write(outfile, format='gwf')
    return outfile


# # -- unit tests -------------------------------------------------------------
def test_read(expected_ts, expected_ts_file):
    # test reading primary TimeSeries file
    actual_ts = lasso.get_primary_ts(
        filepath=expected_ts_file,
        channel=TEST_CHANNEL,
        start=TEST_START,
        end=TEST_END,
        cache=None,
        nproc=1)
    assert actual_ts.t0 == expected_ts.t0
    assert actual_ts.times[-1] == expected_ts.times[-1]
    assert actual_ts.sample_rate == expected_ts.sample_rate
    assert actual_ts.dx == expected_ts.dx
    np.testing.assert_array_equal(
        actual_ts.value,
        expected_ts.value,
        err_msg='read in data array does not match')
