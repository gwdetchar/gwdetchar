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
from .core import (
    write_status,
)

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

logger = cli.logger('gwdetchar.nagios')


# -- main routine ---------------------------------------------------------

def main(args=None):  # pragma: no-cover
    # define command-line arguments
    parser = cli.create_parser(description=__doc__)
    parser.add_argument('code', type=int,
                        help='exit code for Nagios, should be one of: '
                             '0 (success), 1 (warning), or 2 (critical)')
    parser.add_argument('message', type=str,
                        help='status message for Nagios')
    parser.add_argument('-t', '--timeout', type=int, default=0,
                        help='timeout length in seconds, default: no timeout')
    parser.add_argument('-m', '--timeout-message', default='Process timed out',
                        help='Error message upon timeout')
    parser.add_argument('-o', '--output-file', default='nagios.json',
                        help='full path to the output JSON file, '
                             'default: %(default)s')

    # parse arguments
    args = parser.parse_args(args)
    code = args.code
    message = args.message
    timeout = args.timeout
    tmessage = args.timeout_message
    nagiosfile = args.output_file

    # write nagios file
    write_status(message, code, timeout=timeout,
                 tmessage=tmessage, nagiosfile=nagiosfile)

    # log file path
    abspath = os.path.abspath(nagiosfile)
    logger.info('Status written to {}'.format(abspath))


if __name__ == '__main__':  # pragma: no-cover
    sys.exit(main())
