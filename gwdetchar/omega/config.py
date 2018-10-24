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
Configuration files for Omega scans
###################################

How to write a configuration file
=================================

`gwdetchar-omega` can be used to process an arbitrary list of channels,
including primary gravitational wave strain channels and auxiliary sensors,
with arbitrary units and sample rates. Channels can be organized in contextual
blocks using an INI-formatted configuration file that must be passed at
runtime, which must include processing options for individual blocks. In a
given block, the following keywords are supported:

[blockkey]
-------

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
                         ``--ignore-state-flags`` on the command line;
                         optional)
``duration``             The duration of data to process in this block
                         (required)
``fftlength``            The FFT length to use in computing an ASD for
                         whitening with an overlap of `fftlength/2` (required)
``max-mismatch``         The maximum mismatch in time-frequency tiles
                         (optional)
``snr-threshold``        Threshold on SNR for plotting eventgrams (optional)
``always-plot``          Always analyze this block regardless of channel
                         significance (optional; will be superceded by
                         `state-flag` unless `--ignore-state-flags` is passed)
``plot-time-durations``  Time-axis durations of Omega scan plots (required)
``channels``             Full list of channels which appear in this block
                         (required)
=======================  ======================================================

.. code-block:: ini

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

  If running on a LIGO Data Grid (LDG) computer cluster,
  the `~detchar` account houses default configurations organized by subsystem.
"""

try:  # python 3.x
    import configparser
except ImportError:  # python 2.x
    import ConfigParser as configparser

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

OMEGA_DEFAULTS = {}


# -- define parser ------------------------------------------------------------

class OmegaConfigParser(configparser.ConfigParser):
    def __init__(self, ifo=None, defaults=dict(), **kwargs):
        if ifo is not None:
            defaults.setdefault('IFO', ifo)
        configparser.ConfigParser.__init__(self, defaults=defaults, **kwargs)
        self.set_omega_defaults()

    def set_omega_defaults(self):
        for section in OMEGA_DEFAULTS:
            self.add_section(section)
            for key, val in OMEGA_DEFAULTS[section].iteritems():
                if key.endswith('channels') and isinstance(val, (tuple, list)):
                    self.set(section, key, '\n'.join(list(val)))
                elif isinstance(val, tuple):
                    self.set(section, key, ', '.join(map(str, val)))
                else:
                    self.set(section, key, str(val))

    def read(self, filenames):
        readok = configparser.ConfigParser.read(self, filenames)
        for f in filenames:
            if f not in readok:
                raise IOError("Cannot read file %r" % f)
        return readok
    read.__doc__ = configparser.ConfigParser.read.__doc__

    def getfloats(self, section, option):
        return self._get(section, comma_separated_floats, option)

    def getparams(self, section, prefix):
        nchar = len(prefix)
        params = dict((key[nchar:], val) for (key, val) in
                      self.items(section) if key.startswith(prefix))
        # try simple typecasting
        for key in params:
            if params[key].lower() in ('true', 'false'):
                params[key] = bool(params[key])
            if key == 'frequency-range':
                params[key] = tuple([float(s) for s in params[key].split(',')])
            if key == 'channels':
                params[key] = params[key].split(',\n')
            else:
                try:
                    params[key] = float(params[key])
                except ValueError:
                    pass
        return params


def comma_separated_floats(string):
    return map(float, string.split(','))
