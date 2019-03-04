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

"""Lasso regression utilities
"""

from math import log

import numpy
from scipy.interpolate import UnivariateSpline

from sklearn.linear_model import Lasso

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Macedo, Jeff Bidler, Oli Patane, Marissa Walker, ' \
              'Alex Urban, Josh Smith'


# -- utilities ----------------------------------------------------------------

def find_outliers(ts, N=5):
    """Find outliers within a `TimeSeries`

    Parameters
    ----------
    ts : `~gwpy.timeseries.TimeSeries`
        data to find outliers within

    N : `float`, optional
        number of standard deviations to consider an outlier, default: 5

    Returns
    -------
    out : `ndarray`
        array indices of the input where outliers occur
    """
    ts = ts.value  # strip out Quantity extras
    return numpy.nonzero(abs(ts - ts.mean()) > N*ts.std())[0]


def remove_outliers(ts, N=5):
    """Find and remove outliers within a `TimeSeries`

    Parameters
    ----------
    ts : `~gwpy.timeseries.TimeSeries`
        data to find outliers within

    N : `float`, optional
        number of standard deviations to consider an outlier, default: 5

    Notes
    -----
    This action is done in-place, with no `return` statement.
    """
    outliers = find_outliers(ts, N=N)
    c = 1
    while outliers.any():
        print("-- Pass %d: removing %d outliers in %s"
              % (c, outliers.size, ts.name))
        unit = ts.unit
        cache = outliers
        mask = numpy.ones(ts.size, dtype=bool)
        mask[outliers] = False
        spline = UnivariateSpline(ts.times.value[mask], ts.value[mask],
                                  s=0, k=3)
        ts[outliers] = spline(ts.times.value[outliers]) * unit
        outliers = find_outliers(ts, N=N)
        print("   Completed %d removal passes" % c)
        if numpy.array_equal(outliers, cache):
            print("   Outliers did not change, breaking recursion")
            break
        print("   %d outliers remain" % len(outliers))
        c += 1


def fit(data, target, alpha=None):
    """Fit some data to the target using a Lasso model

    Parameters
    ----------
    data : `numpy.ndarray`
        the data

    target : `numpy.ndarray`
        the target data

    alpha : `float`
        the Lasso alpha parameter, if `None` one will be determined using
        :func:`find_alpha`

    Returns
    -------
    model : `~sklearn.linear_model.Lasso`
        the fitted model
    """
    if alpha is None:
        alpha = find_alpha(data, target)
    model = Lasso(alpha)
    return model.fit(data, target)


def find_alpha(data, target):
    """Find the best alpha value to use for the given data
    """
    # build list of alphas
    num = 100
    alphas = numpy.logspace(-1, 0, num, endpoint=True)
    nchans = numpy.zeros(num)
    coef_path = numpy.zeros((data.shape[1], num))

    # fit each alpha
    for i, alpha in enumerate(alphas):
        model = fit(data, target, alpha=alpha)
        nchans[i] = numpy.nonzero(model.coef_)[0].size
        coef_path[:, i] = model.coef_

    # prune zeros
    nonzero = nchans.nonzero()[0]
    alphas = alphas[nonzero]
    nchans = nchans[nonzero]
    coef_path = coef_path.take(nonzero, axis=1)

    # determine best alpha
    nsamps = data.shape[0]
    mean_squared_error = numpy.mean(
        (target[:, numpy.newaxis] - numpy.dot(data, coef_path)) ** 2,
        axis=0)
    sigma2 = numpy.var(target)
    eps64 = numpy.finfo('float64').eps
    criterion = (nsamps * mean_squared_error / (sigma2 + eps64)
                 + log(nsamps) * nchans)  # Eqns. 2.15--16 in (Zou et al, 2007)
    n_best = numpy.argmin(criterion)
    return alphas[n_best]


def remove_flat(tsdict):
    """Remove flat timeseries from a `TimeSeriesDict`
    """
    outdict = tsdict.copy()
    for key in tsdict.keys():
        series = tsdict[key].value
        if series.min() == series.max():
            outdict.pop(key)
    return outdict


def remove_bad(tsdict):
    """Remove data that cannot be scaled from a `TimeSeriesDict`
    """
    outdict = tsdict.copy()
    for key in tsdict.keys():
        series = tsdict[key].value
        if numpy.isnan(series).any() or numpy.isinf(series).any():
            outdict.pop(key)
    return outdict
