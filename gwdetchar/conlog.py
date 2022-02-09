# coding=utf-8
# Copyright (C) LIGO Scientific Collaboration (2019)
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

"""Check whether state records have changed between two reference times
"""

import gwdatafind
import numpy
import os
import re
import sys

from gwpy.io import gwf as io_gwf
from gwpy.table import EventTable

from . import cli
from .io.datafind import get_data

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = ('Andrew Lundgren <andrew.lundgren@ligo.org>, '
               'Joshua Smith <joshua.smith@ligo.org>, '
               'Duncan Macleod <duncan.macleod@ligo.org>')

# set up logger
PROG = ('python -m gwdetchar.conlog' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())


# -- utilities ----------------------------------------------------------------

def _discover_data_source(obs, frametype, start, end, preview):
    """Determine filepaths to local gravitational-wave frame files
    """
    # get paths to frame files
    cache1 = gwdatafind.find_urls(
        obs,
        frametype,
        start - preview,
        start,
    )
    cache2 = gwdatafind.find_urls(
        obs,
        frametype,
        end,
        end + 1,
    )
    return (cache1, cache2)


def _discover_data(channels, caches, start, end, preview, nproc=1):
    """Load timeseries data from local gravitational-wave frame files
    """
    (cache1, cache2) = caches
    # get data from frames
    data1 = get_data(
        channels,
        start=start - preview,
        end=start,
        source=cache1,
        nproc=nproc,
        verbose='Reading initial data:'.rjust(30),
    )
    data2 = get_data(
        channels,
        start=end,
        end=end + 1,
        source=cache2,
        nproc=nproc,
        verbose='Reading final data:'.rjust(30),
    )
    return (data1, data2)


def _get_available_channels(caches):
    """Determine available channels from local gravitational-wave frame files
    """
    (cache1, cache2) = caches
    try:
        available = (
            set(io_gwf.iter_channel_names(cache1[-1])) &
            set(io_gwf.iter_channel_names(cache2[0]))
        )
    except (IndexError, TypeError):
        raise RuntimeError("Could not find data in the time range requested")
    return available


# -- parse command-line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize argument parser
    parser = cli.create_parser(
        prog=PROG,
        description=__doc__,
    )

    # set arguments from the cli module
    cli.add_gps_start_stop_arguments(parser)
    cli.add_ifo_option(parser)
    cli.add_frametype_option(parser,
                             help='the frametype name, defaults to second '
                                  'trends for the selected interferometer')
    cli.add_nproc_option(parser)

    # other optional arguments
    parser.add_argument(
        '-o',
        '--output',
        default='changes.csv',
        help='Path to output data file, default: %(default)s',
    )
    parser.add_argument(
        '-c',
        '--channels',
        default=None,
        required=False,
        help='file containing columnar list of channels to '
             'process, default is to find all relevant channels '
             'from frames',
    )
    parser.add_argument(
        '-s',
        '--search',
        nargs='*',
        default=[],
        help='process channels matching these regex patterns, '
             'can be given multiple times, default is to analyze '
             'all relevant channels from frames',
    )
    parser.add_argument(
        '-p',
        '--preview',
        default=10,
        type=int,
        help='Time (seconds) over which to test that channel is '
             'normally kept constant, default: %(default)s',
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the Conlog command-line tool
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # get IFO and frametype
    ifo = args.ifo.upper()
    obs = ifo[0]
    frametype = args.frametype or '{}_T'.format(ifo)
    preview_time = max(1, args.preview)

    # get paths to frame files
    (cache1, cache2) = _discover_data_source(
        obs,
        frametype,
        args.gpsstart,
        args.gpsend,
        preview_time,
    )

    # get list of channels to analyze
    LOGGER.info('Determining channels to analyze')
    available = _get_available_channels((cache1, cache2))
    if args.channels:
        reqchannels = set(numpy.loadtxt(args.channels, dtype=str, ndmin=1))
        channels = list(reqchannels & available)
    else:
        channels = [x for x in available if x.endswith('.mean')]
    if args.search:  # if requested, get channels matching regex patterns
        re_requested = re.compile('({})'.format('|'.join(args.search)))
        channels = [x for x in channels if re_requested.search(x)]
    LOGGER.debug('Found {} channels in frames'.format(len(channels)))

    # get data from frames
    (data1, data2) = _discover_data(
        channels,
        (cache1, cache2),
        args.gpsstart,
        args.gpsend,
        preview_time,
        nproc=args.nproc,
    )

    # initialize columns
    LOGGER.debug('Analyzing {} channels'.format(len(data1)))
    changes = []
    value1 = []
    value2 = []
    diff = []

    # identify channels
    for channel in data1:
        xoft1 = data1[channel].value
        xoft2 = data2[channel].value
        if numpy.any(numpy.diff(xoft1) != 0):
            continue
        if xoft1[-1] == xoft2[0]:
            continue
        changes.append(channel)
        value1.append(xoft1[-1])
        value2.append(xoft2[0])
        diff.append(xoft2[0] - xoft1[-1])

    # record output
    LOGGER.debug('Analysis complete')
    table = EventTable([changes, value1, value2, diff],
                       names=('channel', 'initial_value',
                              'final_value', 'difference'))

    # log output
    LOGGER.info('The following {0} channels record a state '
                'change between {1} and {2}:\n\n'.format(
                    len(changes),
                    args.gpsstart,
                    args.gpsend,
                ))
    print(table)
    print('\n\n')

    # save output
    table.write(args.output, overwrite=True)
    LOGGER.info('Output written to {}'.format(args.output))


# -- run code -----------------------------------------------------------------

if __name__ == "__main__":
    main()
