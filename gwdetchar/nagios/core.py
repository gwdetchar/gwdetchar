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

"""Utilities for providing status updates to Nagios
"""

import os
import json

from gwpy.time import to_gps

__author__ = 'Alex Urban <alexander.urban@ligo.org>'


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
