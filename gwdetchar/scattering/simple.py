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

"""Simple command-line interface to gwdetchar.scattering

Given a specific GPS time of interest, this module scans through records of
optic motion and projects fringe frequencies due to optical scattering. For
those channels with fringes above a user-specified threshold, a plot is
created comparing the fringes to a high-resolution Q-scan spectrogram.

To identify broader time segments when scattering is likely in the first
place, please use the main command-line module:

python -m gwdetchar.scattering --help
"""

import os
import sys

from gwpy.time import to_gps

from .. import (cli, const)
from ..omega import highpass
from ..io.datafind import get_data

from . import (
    OPTIC_MOTION_CHANNELS,
    get_fringe_frequency,
)

from matplotlib import use
use('Agg')

# backend-dependent import
from . import plot  # noqa: E402

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Joshua Smith <joshua.smith@ligo.org>' \
              'Andrew Lundgren <andrew.lundgren>@ligo.org>' \
              'Duncan Macleod <duncan.macleod@ligo.org>'

# global variables

ASD_KW = {
    'method': 'median',
    'fftlength': 8,
    'overlap': 4,
}

MOTION_CHANNELS = [channel for key in OPTIC_MOTION_CHANNELS.keys()
                   for channel in OPTIC_MOTION_CHANNELS[key]]

PROG = ('python -m gwdetchar.scattering.simple' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())


# -- utilities ----------------------------------------------------------------

def _discover_data(primary, channels, start, end,
                   primary_frametype, aux_frametype):
    """Load timeseries data from local gravitational-wave frame files
    """
    hoft = get_data(
        primary,
        start=start - ASD_KW['overlap'],
        end=end + ASD_KW['overlap'],
        frametype=primary_frametype,
        verbose='Reading primary channel:'.rjust(30),
    )
    aux = get_data(
        channels,
        start=start,
        end=end,
        frametype=aux_frametype,
        verbose='Reading auxiliary sensors:'.rjust(30),
    )
    return (hoft, aux)


# -- parse command-line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize argument parser
    parser = cli.create_parser(
        prog=PROG,
        description=__doc__,
    )

    # required arguments
    parser.add_argument(
        'gpstime',
        type=to_gps,
        help='GPS time or datestring to analyze',
    )
    cli.add_ifo_option(
        parser,
        ifo=const.IFO,
    )

    # optional arguments
    parser.add_argument(
        '-d',
        '--duration',
        type=float,
        default=60,
        help='Duration (seconds) of analysis, default: 60',
    )
    parser.add_argument(
        '-t',
        '--frequency-threshold',
        type=float,
        default=15,
        help='critical fringe frequency threshold (Hz), '
             'default: %(default)s',
    )
    parser.add_argument(
        '-m',
        '--multipliers',
        default='1,2,4,8',
        help='harmonic numbers to plot projected motion for, '
             'should be given as a comma-separated list of '
             'numbers, default: %(default)s',
    )
    parser.add_argument(
        '-x',
        '--multiplier-for-threshold',
        type=int,
        default=4,
        help='frequency multiplier to use when applying '
             '--frequency-threshold, default: %(default)s',
    )
    parser.add_argument(
        '-w',
        '--primary-channel',
        default='GDS-CALIB_STRAIN',
        help='name of primary channel (without IFO prefix), '
             'default: %(default)s',
    )
    parser.add_argument(
        '-W',
        '--primary-frametype',
        default='{IFO}_HOFT_C00',
        help='frametype from which to read primary channel, '
             'default: %(default)s',
    )
    parser.add_argument(
        '-a',
        '--aux-frametype',
        default='{IFO}_R',
        help='frametype from which to read auxiliary channels, '
             'default: %(default)s',
    )
    parser.add_argument(
        '-o',
        '--output-dir',
        type=os.path.abspath,
        default=os.curdir,
        help='Output directory for analysis, default: %(default)s',
    )
    parser.add_argument(
        '-c',
        '--colormap',
        default='viridis',
        help='name of colormap to use, default: %(default)s',
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the simple version of the scattering command-line tool
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # store arguments
    ifo = args.ifo
    gps = float(args.gpstime)
    gpsstart = gps - 0.5 * args.duration
    gpsend = gps + 0.5 * args.duration
    primary = ':'.join([ifo, args.primary_channel])
    channels = [':'.join([ifo, c]) for c in MOTION_CHANNELS]
    thresh = args.frequency_threshold
    multipliers = [int(x) for x in args.multipliers.split(',')]
    harmonic = args.multiplier_for_threshold
    if '{IFO}' in args.primary_frametype:
        args.primary_frametype = args.primary_frametype.format(IFO=ifo)
    if '{IFO}' in args.aux_frametype:
        args.aux_frametype = args.aux_frametype.format(IFO=ifo)
    LOGGER.info('{0} Scattering: {1}'.format(ifo, gps))

    # retrieve data
    (hoft, data) = _discover_data(primary, channels, gpsstart, gpsend,
                                  args.primary_frametype, args.aux_frametype)

    # set up spectrogram
    LOGGER.debug('Setting up a Q-scan spectrogram of {}'.format(primary))
    hoft = highpass(hoft, f_low=thresh).resample(256)
    qspecgram = hoft.q_transform(qrange=(4, 150), frange=(0, 60), gps=gps,
                                 fres=0.1, outseg=(gpsstart, gpsend), **ASD_KW)
    qspecgram.name = primary

    # process channels
    count = 0  # running count of plots written
    for channel in channels:
        LOGGER.info(' -- Processing {} -- '.format(channel))
        try:
            motion = data[channel].detrend().resample(128)
        except KeyError:
            LOGGER.warning('Skipping {}'.format(channel))
            continue
        # project scattering frequencies
        fringe = get_fringe_frequency(motion, multiplier=1)
        ind = fringe.argmax()
        fmax = fringe.value[ind]
        tmax = fringe.times.value[ind]
        LOGGER.debug('Maximum scatter frequency {0:.2f} Hz at GPS second '
                     '{1:.2f}'.format(fmax, tmax))
        if harmonic * fmax < thresh:
            LOGGER.warning('No significant evidence of scattering '
                           'found in {}'.format(channel))
            continue
        # plot spectrogram and fringe frequency
        output = os.path.join(
            args.output_dir,
            '%s-%s-%s-{}.png' % (
                channel.replace('-', '_').replace(':', '-', 1),
                gps, args.duration)
        )
        LOGGER.debug('Plotting spectra and projected fringe frequencies')
        plot.spectral_comparison(
            gps, qspecgram, fringe, output.format('comparison'), thresh=thresh,
            multipliers=multipliers, colormap=args.colormap)
        plot.spectral_overlay(
            gps, qspecgram, fringe, output.format('overlay'),
            multipliers=multipliers)
        LOGGER.info(' -- Channel complete -- ')
        count += 1  # increment counter
    LOGGER.info('{0:g} chanels plotted in {1}'.format(count, args.output_dir))


# -- run from command-line ----------------------------------------------------

if __name__ == '__main__':
    main()
