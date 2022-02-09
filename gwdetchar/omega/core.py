# coding=utf-8
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
# along with GW DetChar.  If not, see <http://www.gnu.org/licenses/>.

"""Core utilities for implementing omega scans
"""

from scipy.signal import butter

from gwpy.segments import Segment
from gwpy.signal.qtransform import q_scan

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# -- basic utilities ----------------------------------------------------------

def highpass(series, f_low, order=12, analog=False, ftype='sos'):
    """High-pass a `TimeSeries` with a Butterworth filter

    Parameters
    ----------
    series : `~gwpy.timeseries.TimeSeries`
        the `TimeSeries` data to high-pass filter

    f_low : `float`
        lower cutoff frequency (Hz) of the filter

    order : `int`, optional
        number of taps in the filter, default: 12

    analog : `bool`, optional
        when True, return an analog filter, otherwise a digital filter is
        returned, default: False

    ftype : `str`, optional
        type of filter: numerator/denominator (`'ba'`), pole-zero (`'zpk'`), or
        second-order sections (`'sos'`), default: `'sos'`

    Returns
    -------
    hpseries : `~gwpy.timeseries.TimeSeries`
        the high-passed `TimeSeries`

    Notes
    -----
    This utility designs a Butterworth filter of order `order` with corner
    frequency `f_low / 1.5`, then applies this filter to the input.

    See Also
    --------
    scipy.signal.butter
    gwpy.timeseries.TimeSeries.filter
    """
    corner = f_low / 1.5
    fs = series.sample_rate.to('Hz').value
    hpfilt = butter(order, corner, btype='highpass', analog=analog,
                    output=ftype, fs=fs)
    hpseries = series.filter(hpfilt, filtfilt=True)
    return hpseries


def whiten(series, fftlength, overlap=None, method='median', window='hann',
           detrend='linear'):
    """Whiten a `TimeSeries` against its own ASD

    Parameters
    ----------
    series : `~gwpy.timeseries.TimeSeries`
        the `TimeSeries` data to whiten

    fftlength : `float`
        FFT integration length (in seconds) for ASD estimation

    overlap : `float`, optional
        seconds of overlap between FFTs, defaults to half the FFT length

    method : `str`, optional
        FFT-averaging method, default: ``'median'``,

    window : `str`, `numpy.ndarray`, optional
        window function to apply to timeseries prior to FFT,
        default: ``'hann'``
        see :func:`scipy.signal.get_window` for details on acceptable
        formats

    detrend : `str`, optional
        type of detrending to do before FFT, default: ``'linear'``

    Returns
    -------
    wseries : `~gwpy.timeseries.TimeSeries`
        a whitened version of the input data with zero mean and unit variance

    See Also
    --------
    gwpy.timeseries.TimeSeries.whiten
    """
    # get overlap window and whiten
    if overlap is None:
        overlap = fftlength / 2
    return series.whiten(fftlength=fftlength, overlap=overlap, window=window,
                         detrend=detrend, method=method).detrend(detrend)


# -- omega scans --------------------------------------------------------------

def conditioner(xoft, fftlength, overlap=None, resample=None, f_low=None,
                **kwargs):
    """Condition some input data for an omega scan

    Parameters
    ----------
    xoft : `~gwpy.timeseries.TimeSeries`
        the `TimeSeries` data to whiten

    fftlength : `float`
        FFT integration length (in seconds) for ASD estimation

    overlap : `float`, optional
        seconds of overlap between FFTs, defaults to half the FFT length

    resample : `int`, optional
        desired sampling rate (Hz) of the output if different from the input,
        default: no resampling

    f_low : `float`, optional
        lower cutoff frequency (Hz) of the filter, default: ``None``

    **kwargs : `dict`, optional
        additional arguments to :func:`highpass`

    Returns
    -------
    wxoft : `~gwpy.timeseries.TimeSeries`
        a whitened version of the input data with zero mean and unit variance

    hpxoft : `~gwpy.timeseries.TimeSeries`
        high-passed version of the input data (returned only if `f_low` is
        not ``None``)

    xoft : `~gwpy.timeseries.TimeSeries`
        original (possibly resampled) version of the input data
    """
    if resample:
        xoft = xoft.resample(resample)
    # get whitened and high-passed data streams
    if f_low is None:
        wxoft = whiten(xoft, fftlength, overlap=overlap)
        return (wxoft, xoft)
    else:
        hpxoft = highpass(xoft, f_low, **kwargs)
        wxoft = whiten(hpxoft, fftlength, overlap=overlap)
        return (wxoft, hpxoft, xoft)


def primary(gps, length, hoft, fftlength, resample=None, f_low=None,
            **kwargs):
    """Condition the primary channel for use as a matched-filter

    Parameters
    ----------
    gps : `float`
        GPS time (seconds) of suspected transient

    length : `float`
        length (seconds) of the desired matched-filter

    hoft : `~gwpy.timeseries.TimeSeries`
        the `TimeSeries` data to whiten

    fftlength : `float`
        FFT integration length (in seconds) for ASD estimation

    resample : `int`, optional
        desired sampling rate (Hz) of the output if different from the input,
        default: no resampling

    f_low : `float`, optional
        lower cutoff frequency (Hz) of the filter, default: `None`

    **kwargs : `dict`
        additional keyword arguments to `omega.conditioner`

    Returns
    -------
    out : `~gwpy.timeseries.TimeSeries`
        the conditioned data stream
    """
    if f_low is None:
        out, _ = conditioner(hoft, fftlength, resample=resample)
    else:
        out, _, _ = conditioner(
            hoft, fftlength, resample=resample, f_low=f_low, **kwargs)
    return out.crop(gps - length/2, gps + length/2).taper()


def cross_correlate(xoft, hoft):
    """Cross-correlate two `TimeSeries` by matched-filter

    Parameters
    ----------
    xoft : `~gwpy.timeseries.TimeSeries`
        the `TimeSeries` data to analyze

    hoft : `~gwpy.timeseries.TimeSeries`
        a `TimeSeries` data to use as a matched-filter

    Returns
    -------
    out : `~gwpy.timeseries.TimeSeries`
        the output of a single phase matched-filter
    """
    # make sure series have consistent sample rates
    if hoft.sample_rate.value < xoft.sample_rate.value:
        xoft = xoft.resample(hoft.sample_rate.value)
    elif hoft.sample_rate.value > xoft.sample_rate.value:
        hoft = hoft.resample(xoft.sample_rate.value)
    out = xoft.correlate(hoft, window='hann')
    return out


def scan(gps, channel, xoft, fftlength, resample=None, fthresh=1e-10,
         search=0.5, nt=1400, nf=700, logf=True, **kwargs):
    """Scan a channel for evidence of transients

    Parameters
    ----------
    gps : `float`
        the GPS time (seconds) to scan

    channel : `OmegaChannel`
        `OmegaChannel` object corresponding to this data stream

    xoft : `~gwpy.timeseries.TimeSeries`
        the `TimeSeries` data to analyze

    fftlength : `float`
        FFT integration length (in seconds) for ASD estimation

    resample : `int`, optional
        desired sampling rate (Hz) of the output if different from the input,
        default: no resampling

    fthresh : `float`, optional
        threshold on false alarm rate (Hz) for this channel to be considered
        interesting, default: 1e-10

    search : `float`, optional
        time window (seconds) around `gps` in which to find peak energies,
        default: 0.5

    nt : `int`, optional
        number of points on the time axis of the interpolated `Spectrogram`,
        default: 1400

    nf : `int`, optional
        number of points on the frequency axis of the interpolated
        `Spectrogram`, default: 700

    logf : `bool`, optional
        boolean switch to enable (`True`) or disable (`False`) use of
        log-sampled frequencies in the output `Spectrogram`, default: `True`

    **kwargs : `dict`, optional
        additional arguments to `omega.conditioner`

    Returns
    -------
    series : `tuple`
        an ordered collection of intermediate data products from this scan,
        including: the resampled `TimeSeries`, high-passed `TimeSeries`,
        whitened `TimeSeries`, whitened `QGram`, high-passed `QGram`,
        interpolated whitened `Spectrogram`, and interpolated high-passed
        `Spectrogram`
    """
    # condition data
    wxoft, hpxoft, xoft = conditioner(
        xoft, fftlength, resample=resample, f_low=channel.frange[0], **kwargs)
    # compute whitened Q-gram
    search = Segment(gps - search/2, gps + search/2)
    qgram, far = q_scan(
        wxoft, mismatch=channel.mismatch, qrange=channel.qrange,
        frange=channel.frange, search=search)
    if (far >= fthresh) and (not channel.always_plot):
        return None  # series is insignificant
    # compute raw Q-gram
    Q = qgram.plane.q
    rqgram, _ = q_scan(
        hpxoft, mismatch=channel.mismatch, qrange=(Q, Q),
        frange=qgram.plane.frange, search=search)
    # compute interpolated spectrograms
    tres = min(channel.pranges) / nt
    fres = nf if logf else (
        channel.frange[1] - channel.frange[0]) / nf
    outseg = Segment(
        gps - max(channel.pranges)/2,
        gps + max(channel.pranges)/2,
    )
    qspec = qgram.interpolate(
        tres=tres,
        fres=fres,
        logf=logf,
        outseg=outseg,
    )
    rqspec = rqgram.interpolate(
        tres=tres,
        fres=fres,
        logf=logf,
        outseg=outseg,
    )
    return (xoft, hpxoft, wxoft, qgram, rqgram, qspec, rqspec)
