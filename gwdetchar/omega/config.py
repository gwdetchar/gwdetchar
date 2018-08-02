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
Configuration files for Omega Scans
###################################

How to write a configuration file
=================================
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
