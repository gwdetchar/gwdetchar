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

"""gw_data_find wrappers
"""

from __future__ import print_function

import os.path

from six import string_types

from glue import datafind

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def find_frames(site, frametype, gpsstart, gpsend, **kwargs):
    """Find frames for given site and frametype
    """
    # connect
    host = kwargs.pop('host', None)
    port = kwargs.pop('port', None)
    port = port and int(port)
    if port is not None and port != 80:
        cert, key = datafind.find_credential()
        connection = datafind.GWDataFindHTTPSConnection(
            host=host, port=port, cert_file=cert, key_file=key)
    else:
        connection = datafind.GWDataFindHTTPConnection(host=host, port=port)
    # find frames
    kwargs.setdefault('urltype', 'file')
    return connection.find_frame_urls(site[0], frametype, gpsstart, gpsend,
                                      **kwargs)


def write_omega_cache(cache, fobj):
    """Write a :class:`~glue.lal.Cache` of files to file in Omega format

    The Omega pipeline expects a file cache in a specific, custom format:

    {observatory} {frametype} {gpsstart} {gpsend} {fileduration} {directory}
    """
    # open filepath
    if isinstance(fobj, string_types):
        with open(fobj, 'w') as f:
            return write_omega_cache(cache, f)

    # convert to omega cache format
    wcache = {}
    for e in cache:
        dir_ = os.path.split(e.path)[0]
        if dir_ in wcache:
            l = wcache[dir_]
            if l[2] > int(e.segment[0]):
                wcache[dir_][2] = e.segment[0]
            if l[3] < int(e.segment[1]):
                wcache[dir_][3] = e.segment[1]
        else:
            wcache[dir_] = [e.observatory, e.description,
                            int(e.segment[0]), int(e.segment[1]),
                            int(abs(e.segment)), dir_]

    # write to file
    for item in wcache:
        print(' '.join(map(str, wcache[item])), file=fobj)
