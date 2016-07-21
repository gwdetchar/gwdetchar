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

"""Methods and utilties for performing Omega pipline scans
"""

import re
import os
import subprocess

from gwpy.detector import (Channel, ChannelList)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

OMEGA_LOCATION = os.getenv('OMEGA_LOCATION', None)
WPIPELINE = OMEGA_LOCATION and os.path.join(OMEGA_LOCATION, 'bin', 'wpipeline')

# -- utilities ----------------------------------------------------------------

def get_omega_version(executable='/home/omega/opt/omega/bin/wpipeline'):
    """Determine the omega version from the executable

    >>> get_omega_version()
    'r3449'
    """
    cmd = [executable, 'version']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise subprocess.CalledProcessError(p.returncode, ' '.join(cmd))
    return out.split('\n')[0].split(' ')[-1]


# -- scan configuration parsing -----------------------------------------------

class OmegaChannel(Channel):
    """Sub-class of `~gwpy.detector.Channel` to hold Omega-scan configurations
    """
    def __init__(self, name, section, **params):
        frametype = params.get('frameType', None)
        sampling = params.get('sampleFrequency', None)
        super(OmegaChannel, self).__init__(name, frametype=frametype,
                                           sample_rate=sampling)
        self.section = section.strip('[').rstrip(']\n').split(',', 1)
        self.params = params.copy()


class OmegaChannelList(ChannelList):
    @classmethod
    def read(cls, filename):
        """Parse an Omega-scan configuration file into a `ChannelList`

        Parameters
        ----------
        filename : `str`
            path of Omega configuration file to parse

        Returns
        -------
        channels : `OmegaChannelList`
            the list of channels (in order) as parsed

        Raises
        ------
        RuntimeError
            if this method finds a line it cannot parse sensibly
        """
        out = cls()
        with open(filename, 'r') as fp:
            section = None
            while True:
                try:
                    line = fp.next()
                except StopIteration:
                    break
                if line == '' or line == '\n' or line.startswith('#'):
                    continue
                elif line.startswith('['):
                    section = line[1:-2]
                elif line.startswith('{'):
                    out.append(parse_omega_channel(fp, section))
                else:
                    raise RuntimeError("Failed to parse Omega config line:\n%s"
                                       % line)
        return out


def parse_omega_channel(fp, section=None):
    """Parse a `Channel` from an Omega-scan configuration file

    Parameters
    ----------
    fp : `file`
        the open file-like object to parse
    section : `str`
        name of section in which this channel should be recorded

    Returns
    -------
    channel : `~gwdetchar.omega.OmegaChannel`
        the channel as parsed from this `file`
    """
    params = dict()
    while True:
        line = fp.next()
        if line == '}\n':
            break
        key, value = line.split(':', 1)
        params[key.strip().rstrip()] = omega_param(value)
    return OmegaChannel(params['channelName'], section, **params)


def omega_param(val):
    """Parse a value from an Omega-scan configuration file

    This method tries to parse matlab-syntax parameters into a `str`,
    `float`, or `tuple`
    """
    val = val.strip().rstrip()
    if val.startswith(('"', "'")):
        return str(val[1:-1])
    elif val.startswith('['):
        return tuple(map(float, val[1:-1].split()))
    else:
        return float(val)


# -- scan processing ----------------------------------------------------------

def run(gpstime, config, cachefile, outdir='.', report=True,
        wpipeline=WPIPELINE, colormap='parula', verbose=False):
    """Run a wpipeline scan at the given GPS time

    Parameters
    ----------
    gpstime : `float`, `~gwpy.time.LIGOTimeGPS`
        the GPS time of the desired scan
    config : `str`
        path to the configuration file
    cachefile : `str`
        path to the frame cache
    outdir : `str`, default: `pwd`
        output directory for this scan
    report : `bool`, default: `True`
        run wpipeline scan in `--report` mode
    wpipeline : `str`
        path to wpipeline executable
    verbose : `bool`
        print verbose output

    Raises
    ------
    subprocess.CalledProcessError
        if the omega scan fails
    """
    if wpipeline is None:
        raise RuntimeError("Unable to determine wpipeline path automatically, "
                           "please give explicitly")
    # create command
    cmd = [wpipeline, 'scan', str(gpstime), '--configuration', config,
           '--framecache', cachefile, '--outdir', outdir]
    if report:
        cmd.append('--report')
    # if omega is new enough, add the --colormap option
    try:
        version = get_omega_version(wpipeline)
    except subprocess.CalledProcessError:
        pass
    else:
        if version >= 'r3449':
            cmd.extend(('--colormap', colormap))
    # RUN
    if verbose:
        print("Running omega scan as\n\n%s\n" % ' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=verbose and subprocess.PIPE or None)
    proc.communicate()
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, ' '.join(cmd))
    if verbose:
        print('Omega scan complete')
