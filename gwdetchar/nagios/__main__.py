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

"""Command-line utility for providing status updates to Nagios
"""

import os
import sys

from .. import cli
from .core import write_status

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

PROG = ('python -m gwdetchar.nagios' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())


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
        'code',
        type=int,
        help='exit code for Nagios, should be one of: '
             '0 (success), 1 (warning), or 2 (critical)',
    )
    parser.add_argument(
        'message',
        type=str,
        help='status message for Nagios',
    )

    # optional arguments
    parser.add_argument(
        '-t',
        '--timeout',
        type=int,
        default=0,
        help='timeout length in seconds, default: no timeout',
    )
    parser.add_argument(
        '-m',
        '--timeout-message',
        default='Process timed out',
        help='Error message upon timeout',
    )
    parser.add_argument(
        '-o',
        '--output-file',
        default='nagios.json',
        help='full path to the output JSON file, '
             'default: %(default)s',
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the command-line Nagios status generator
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # write nagios file
    write_status(
        args.message,
        args.code,
        timeout=args.timeout,
        tmessage=args.timeout_message,
        nagiosfile=args.output_file,
    )

    # log output file path
    LOGGER.info('Status written to {}'.format(
        os.path.abspath(args.output_file)))


# -- run from command-line ----------------------------------------------------

if __name__ == '__main__':
    main()
