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

"""Utilities for providing status updates to Nagios
"""

import os
import sys
import json

from gwpy.time import to_gps

from . import cli

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

logger = cli.logger('gwdetchar.nagios')


# -- utilities ----------------------------------------------------------------

def write_status(message, code, timeout=0, tmessage=None,
                 outdir=os.path.curdir):
    """Write a Nagios status file in JSON format

    Parameters
    ----------
    message : `str`
        status message for Nagios

    code : `int`
        exit code for process

    timeout : `int`, optional
        timeout length, in seconds

    tmessage : `str`, optional
        timeout message

    outdir : `str`, optional
        output directory where JSON file will be written

    Notes
    -----
    This function will write an output file called ``nagios.json`` to the
    given output directory, then exit without returning.
    """
    # status dictionary
    status = {
        "created_gps": int(to_gps('now')),
        "status_intervals": [{
            "start_sec": 0,
            "txt_status": message,
            "num_status": code
        }],
    }
    # update timeout information
    if timeout:
        status["status_intervals"].append({
            "start_sec": timeout,
            "txt_status": tmessage,
            "num_status": 3,
        })
    # get output file and write
    nagiosfile = os.path.join(outdir, 'nagios.json')
    with open(nagiosfile, 'w') as fileobj:
        json.dump(status, fileobj)


# -- main routine ---------------------------------------------------------

def main(args=None):  # pragma: no-cover
    # define command-line arguments
    parser = cli.create_parser(description=__doc__)
    parser.add_argument('code', type=int, required=True,
                        help='exit code for Nagios, should be one of: '
                             '0 (success), 1 (warning), or 2 (critical)')
    parser.add_argument('message', type=str, required=True,
                        help='status message for Nagios')
    parser.add_argument('-t', '--timeout', type=int, default=0,
                        help='timeout length in seconds, default: no timeout')
    parser.add_argument('-m', '--timeout-message', default='Process timed out',
                        help='Error message upon timeout')
    parser.add_argument('-o', '--output-dir', default=os.path.curdir,
                        help='output directory for JSON file, '
                             'default: %(default)s')

    # parse arguments
    args = parser.parse_args(args)
    code = args.code
    message = args.message
    timeout = args.timeout
    tmessage = args.timeout_message
    outdir = args.output_dir

    # write nagios file
    write_status(message, code, timeout=timeout,
                 tmessage=tmessage, outdir=outdir)

    # log file path
    abspath = os.path.join(outdir, 'nagios.json')
    logger.info('Status written to {}'.format(abspath))


if __name__ == '__main__':  # pragma: no-cover
    sys.exit(main())
