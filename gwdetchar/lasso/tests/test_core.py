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

"""Tests for `gwdetchar.lasso`
"""

import numpy
from numpy import testing as nptest

from gwpy.timeseries import (TimeSeries, TimeSeriesDict)

from .. import core

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


# global test objects

IND = 8
IND2 = 25
OUTLIER_IN = numpy.random.normal(loc=0, scale=1, size=1024)
OUTLIER_IN[IND] = 100
OUTLIER_TS = TimeSeries(OUTLIER_IN, sample_rate=1024, unit='Mpc',
                        name='X1:TEST_RANGE')

OUTLIER_IN_PF = numpy.random.normal(loc=0, scale=1, size=100)
OUTLIER_IN_PF[IND] = -100
OUTLIER_IN_PF[IND2] = -75
OUTLIER_TS_PF = TimeSeries(OUTLIER_IN_PF, sample_rate=100, unit='Mpc',
                           name='X1:TEST_RANGE')

TARGET = numpy.array([-1, 0, 1])

SERIES = TimeSeries(TARGET, sample_rate=1, epoch=-1)
DATA = numpy.array([SERIES.value]).T

TSDICT = TimeSeriesDict({
    'full': SERIES,
    'flat': TimeSeries(numpy.ones(3), sample_rate=1, epoch=0),
    'nan': TimeSeries(numpy.full(3, numpy.nan), sample_rate=1, epoch=0),
})


# -- unit tests ---------------------------------------------------------------

def test_find_outliers():
    # test for standard deviation outlier finding
    # find expected outliers using standard deviation method
    outliers = core.find_outliers(OUTLIER_TS)
    assert isinstance(outliers, numpy.ndarray)
    nptest.assert_array_equal(outliers, numpy.array([IND]))


def test_find_outliers_pf():
    # test for percentile outlier finding
    # find expected outliers using percentile range method
    outliers = core.find_outliers(OUTLIER_TS_PF, N=0.01, method='pf')
    assert isinstance(outliers, numpy.ndarray)
    nptest.assert_array_equal(outliers, numpy.array([IND]))


def test_remove_outliers():
    # strip off outliers
    core.remove_outliers(OUTLIER_TS)
    assert OUTLIER_TS[IND] - OUTLIER_TS.mean() <= 5 * OUTLIER_TS.std()


def test_remove_outliers_pf():
    # Strip off outliers
    core.remove_outliers(OUTLIER_TS_PF, N=0.01, method='pf')
    outliers = core.find_outliers(OUTLIER_TS_PF, N=0.01, method='pf')
    assert isinstance(outliers, numpy.ndarray)
    nptest.assert_array_equal(outliers, numpy.array([IND2]))


def test_fit():
    # adapted from unit tests for sklearn.linear_model
    model = core.fit(DATA, TARGET, alpha=1e-8)
    assert model.alpha == 1e-8
    nptest.assert_almost_equal(model.coef_, [1])
    nptest.assert_almost_equal(model.dual_gap_, 0)
    nptest.assert_almost_equal(model.predict([[0], [1]]), [0, 1])


def test_find_alpha():
    # find the optimal alpha parameter
    alpha = core.find_alpha(DATA, TARGET)
    assert alpha == 0.1


def test_remove_flat():
    # remove flat TimeSeries
    tsdict = core.remove_flat(TSDICT)
    assert len(tsdict.keys()) == 2
    assert 'flat' not in tsdict.keys()
    nptest.assert_array_equal(tsdict['full'].value, TSDICT['full'].value)
    nptest.assert_array_equal(tsdict['nan'].value, TSDICT['nan'].value)


def test_remove_bad():
    # remove unscalable TimeSeries
    tsdict = core.remove_bad(TSDICT)
    assert len(tsdict.keys()) == 2
    assert 'nan' not in tsdict.keys()
    nptest.assert_array_equal(tsdict['full'].value, TSDICT['full'].value)
    nptest.assert_array_equal(tsdict['flat'].value, TSDICT['flat'].value)
