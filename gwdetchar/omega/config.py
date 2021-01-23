# coding=utf-8
# Copyright (C) Duncan Macleod (2015)
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

"""
#################################
How to write a configuration file
#################################

:mod:`gwdetchar.omega` can be used to process an arbitrary list of channels,
including primary gravitational wave strain channels and auxiliary sensors,
with arbitrary units and sample rates. Channels can be organized in contextual
blocks using an INI-formatted configuration file that must be passed at
runtime, which must include processing options for individual blocks. In a
given block, the following keywords are supported:

Keywords
--------

=======================  ======================================================
``name``                 The full name of this channel block, which will
                         appear as a section header on the output page
                         (optional)
``parent``               The `blockkey` of a section that the current block
                         should appear on the output page with (optional)
``q-range``              Range of quality factors (or Q) to search (required)
``frequency-range``      Range of frequencies to search (required)
``resample``             A sample rate (in Hz) to resample the input data to,
                         must be different from the original sample rate
                         (optional)
``frametype``            The type of frame files to read data from (will be
                         superceded by `source`, required if `source` is not
                         specified)
``source``               Path to a LAL-format cache pointing to frame files
``state-flag``           A data quality flag to require to be active before
                         processing this block (can be superceded by passing
                         ``--ignore-state-flags`` on the command-line;
                         optional)
``duration``             The duration of data to process in this block
                         (required)
``fftlength``            The FFT length to use in computing an ASD for
                         whitening with an overlap of `fftlength/2` (required)
``search``               Duration (seconds) of search time window (optional)
``max-mismatch``         The maximum mismatch in time-frequency tiles
                         (optional)
``snr-threshold``        Threshold on SNR for plotting eventgrams (optional)
``dt``                   Maximum acceptable time delay from the primary
                         channel (optional)
``always-plot``          Always analyze this block regardless of channel
                         significance (optional; will be superceded by
                         `state-flag` unless `--ignore-state-flags` is passed)
``plot-time-durations``  Time-axis durations of omega scan plots (required)
``channels``             Full list of channels which appear in this block
                         (required)
=======================  ======================================================

If cross-correlation will be implemented, the user will also need to specify
a block whose blockkey is ``primary`` that includes only one ``channel``
and options for ``f-low`` (a high-pass corner frequency) and
``matched-filter-length``. State flags are always ignored for the primary.

An example using many of the above options would look something like this:

.. code-block:: ini

   [primary]
   ; the primary channel, which will be used as a matched-filter
   f-low = 4.0
   resample = 4096
   frametype = L1_HOFT_C00
   duration = 64
   fftlength = 8
   matched-filter-length = 2
   channel = L1:GDS-CALIB_STRAIN

   [GW]
   ; name of this block, which contains h(t)
   name = Gravitational Wave Strain
   q-range = 3.3166,150.0
   frequency-range = 4.0,2048
   resample = 4096
   frametype = L1_HOFT_C00
   state-flag = L1:DMT-GRD_ISC_LOCK_NOMINAL:1
   duration = 64
   fftlength = 8
   max-mismatch = 0.2
   snr-threshold = 5
   always-plot = True
   plot-time-durations = 1,4,16
   channels = L1:GDS-CALIB_STRAIN

   [CAL]
   ; a sub-block of channels with different options, but which should appear
   ; together with the block `GW` on the output page
   parent = GW
   q-range = 3.3166,150
   frequency-range = 4.0,Inf
   resample = 4096
   frametype = L1_R
   state-flag = L1:DMT-GRD_ISC_LOCK_NOMINAL:1
   duration = 64
   fftlength = 8
   max-mismatch = 0.35
   snr-threshold = 5.5
   always-plot = True
   plot-time-durations = 1,4,16
   channels = L1:CAL-DELTAL_EXTERNAL_DQ

.. note::

   The `blockkey` will appear in the navbar to identify channel blocks on the
   output page, with a scrollable dropdown list of channels in that block for
   ease of navigation.

   The `primary` block will only be used to design a matched-filter. To process
   this channel during the omega scan, it must be included again in a
   subsequent block.

   If running on a LIGO Data Grid (LDG) computer cluster, the `~detchar`
   account houses default configurations organized by subsystem.
"""

import sys
import ast
import os.path
import configparser
import numpy

from gwpy.detector import Channel

from .. import const
from ..io.html import FancyPlot

if sys.version_info < (3, 7):
    from collections import OrderedDict

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# -- define parser ------------------------------------------------------------

class OmegaConfigParser(configparser.ConfigParser):
    """Custom configuration parser for :mod:`gwdetchar.omega`

    Parameters
    ----------
    ifo : `str`, optional
        prefix of the interferometer to use, defaults to `None`

    defaults : `dict`, optional
        dictionary of default values to pass to the parser, default: ``{}``

    **kwargs : `dict`, optional
        additional keyword arguments to pass to `ConfigParser`

    Methods
    -------
    read:
        parse a list of INI-format configuration files
    get_channel_blocks:
        retrieve an ordered dictionary of contextual channel blocks, as
        organized in the source configuration
    """
    def __init__(self, ifo=None, defaults=dict(), **kwargs):
        if ifo is not None:
            defaults.setdefault('IFO', ifo)
        configparser.ConfigParser.__init__(self, defaults=defaults, **kwargs)

    def read(self, filenames):
        readok = configparser.ConfigParser.read(self, filenames)
        for f in filenames:
            if f not in readok:
                raise IOError("Cannot read file %r" % f)
        return readok
    read.__doc__ = configparser.ConfigParser.read.__doc__

    def get_channel_blocks(self):
        """Retrieve an ordered dictionary of channel blocks

        These blocks are organized contextually by the user, since they are
        read in and preserved from the source configuration.
        """
        # retrieve an ordered dictionary of channel blocks
        if sys.version_info >= (3, 7):  # python 3.7+
            return {s: OmegaChannelList(s, **self[s]) for s in self.sections()}
        else:
            return OrderedDict([(s, OmegaChannelList(s, **dict(self.items(s))))
                                for s in self.sections()])


# -- utilities ----------------------------------------------------------------

def get_default_configuration(ifo, gpstime):
    """Retrieve a default configuration file stored locally

    Parameters
    ----------
    ifo : `str`
        interferometer ID string, e.g. `'L1'`

    gpstime : `float`
        time of analysis in GPS second format
    """
    # find epoch
    epoch = const.gps_epoch(gpstime, default=const.latest_epoch())
    # find and parse configuration file
    if ifo == 'Network':
        return [os.path.expanduser(
            '~detchar/etc/omega/{epoch}/Network.ini'.format(epoch=epoch))]
    else:
        return [os.path.expanduser(
            '~detchar/etc/omega/{epoch}/{obs}-{ifo}_R-selected.ini'.format(
                epoch=epoch, obs=ifo[0], ifo=ifo))]


def get_fancyplots(channel, plottype, duration, caption=None):
    """Construct FancyPlot objects for output HTML pages

    Parameters
    ----------
    channel : `str`
        the name of the channel

    plottype : `str`
        the type of plot, e.g. 'raw_timeseries'

    duration : `str`
        duration of the plot, in seconds

    caption : `str`, optional
        a caption to render in the fancybox
    """
    plotdir = 'plots'
    chan = channel.replace('-', '_').replace(':', '-')
    filename = '%s/%s-%s-%s.png' % (plotdir, chan, plottype, duration)
    if not caption:
        caption = os.path.basename(filename)
    return FancyPlot(filename, caption)


# -- channel list objects -----------------------------------------------------

class OmegaChannel(Channel):
    """Customized `Channel` object for omega scan analyses

    Parameters
    ----------
    channelname : `str`
        name of this channel, e.g. `L1:GDS-CALIB_STRAIN`

    section : `str`
        configuration section to which this channel belongs

    params : `dict`
        parameters set in a configuration file
    """
    def __init__(self, channelname, section, **params):
        self.name = channelname
        frametype = params.get('frametype', None)
        super(OmegaChannel, self).__init__(
            channelname, frametype=frametype)
        if section != 'primary':
            self.qrange = tuple(
                [float(s) for s in params.get('q-range').split(',')])
            self.frange = tuple(
                [float(s) for s in params.get('frequency-range').split(',')])
            self.mismatch = float(params.get('max-mismatch', 0.2))
            self.snrthresh = float(params.get('snr-threshold', 5.5))
            self.always_plot = ast.literal_eval(
                params.get('always-plot', 'False'))
            self.pranges = [int(t) for t in params.get('plot-time-durations',
                                                       None).split(',')]
            self.plots = {}
            for plottype in ['timeseries_raw', 'timeseries_highpassed',
                             'timeseries_whitened', 'qscan_highpassed',
                             'qscan_whitened', 'qscan_autoscaled',
                             'eventgram_highpassed', 'eventgram_whitened',
                             'eventgram_autoscaled']:
                self.plots[plottype] = [get_fancyplots(self.name, plottype, t)
                                        for t in self.pranges]
        self.section = section
        self.params = params.copy()

    def save_loudest_tile_features(self, qgram, correlate=None, gps=0, dt=0.1):
        """Store properties of the loudest time-frequency tile

        Parameters
        ----------
        channel : `OmegaChannel`
            `OmegaChannel` object corresponding to this data stream

        qgram : `~gwpy.signal.qtransform.QGram`
            output of a Q-transform on whitened input

        correlate : `~gwpy.timeseries.TimeSeries`, optional
            output of a single phase matched-filter, or `None` if not requested

        gps : `float`, optional
            GPS time (seconds) of suspected transient, used only if `correlate`
            is not `None`, default: 0

        dt : `float`, optional
            maximum acceptable time delay (seconds) between the primary and
            `self`, used only if `correlate` is not `None`, default: 0.1

        Notes
        -----
        Attributes stored in-place include `Q`, `energy`, `snr`, `t`, and `f`,
        all corresponding to the loudest time-frequency tile contained in
        `qgram`.

        If `correlate` is not `None` then the maximum correlation amplitude,
        relative time delay, and standard deviation are stored as attributes
        `corr`, `delay`, and `stdev`, respectively.
        """
        # save parameters
        self.Q = numpy.around(qgram.plane.q, 1)
        self.energy = numpy.around(qgram.peak['energy'], 1)
        self.snr = numpy.around(qgram.peak['snr'], 1)
        self.t = numpy.around(qgram.peak['time'], 3)
        self.f = numpy.around(qgram.peak['frequency'], 1)
        if correlate is not None:
            stdev = correlate.std().value
            corr = correlate.abs().crop(gps - dt, gps + dt)
            self.corr = numpy.around(corr.max().value, 1)
            self.stdev = stdev  # used to reject high glitch rates
            delay = (corr.t0 + corr.argmax() * corr.dt).value - gps
            self.delay = int(delay * 1000)  # convert to ms

    def load_loudest_tile_features(self, table, correlated=False):
        """Load properties of the loudest time-frequency tile from a table

        Parameters
        ----------
        table : `~gwpy.table.Table`
            table of properties of the loudest time-frequency tile

        correlated : `bool`, optional
            boolean switch to determine if cross-correlation properties are
            included, default: `False`

        Notes
        -----
        Attributes stored in-place include `Q`, `energy`, `snr`, `t`, and `f`,
        all corresponding to the columns contained in `table`.

        If `correlated` is not `None` then the maximum correlation amplitude,
        relative time delay, and standard deviation are stored as attributes
        `corr`, `delay`, and `stdev`, respectively.
        """
        # save parameters
        self.Q = table['Q']
        self.energy = table['Energy']
        self.snr = table['SNR']
        self.t = table['Central Time']
        self.f = table['Central Frequency (Hz)']
        if correlated:
            self.corr = table['Correlation']
            self.stdev = table['Standard Deviation']
            self.delay = table['Delay (ms)']


class OmegaChannelList(object):
    """A conceptual list of `OmegaChannel` objects with common signal
    processing settings

    Parameters
    ----------
    key : `str`
        the unique identifier for this list, e.g. `'CAL'` for calibration
        channels

    params : `dict`
        parameters set in a configuration file
    """
    def __init__(self, key, **params):
        self.key = key
        self.parent = params.get('parent', None)
        self.name = params.get('name', None)
        self.duration = int(params.get('duration', 32))
        self.fftlength = int(params.get('fftlength', 2))
        self.resample = int(params.get('resample', 0))
        self.source = params.get('source', None)
        self.frametype = params.get('frametype', None)
        section = self.parent if self.parent else self.key
        if key == 'primary':
            self.length = float(params.get('matched-filter-length'))
            self.flow = float(params.get('f-low', 4))
            channelname = params.get('channel').strip()
            self.channel = OmegaChannel(channelname, section, **params)
        else:
            self.flag = params.get('state-flag', None)
            self.search = float(params.get('search', 0.5))
            self.dt = float(params.get('dt', 0.1))
            chans = params.get('channels', None).strip().split('\n')
            self.channels = [OmegaChannel(c, section, **params) for c in chans]
        self.params = params.copy()
