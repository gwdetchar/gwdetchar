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

from glue import datafind

from .. import version

__version__ = version.version
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
