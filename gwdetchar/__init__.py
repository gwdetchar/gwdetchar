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

"""The GW DetChar package (`gwdetchar`) provides python utilies for
Gravitational-wave detector characterisation.

This package extends the GWpy package for gravitational-wave
data processing (https://gwpy.github.io).
"""

from ._version import get_versions

__version__ = get_versions()['version']
__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

del get_versions
