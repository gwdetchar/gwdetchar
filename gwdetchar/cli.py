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

"""Command-line interface utilities for `gwdetchar`
"""

import argparse

from gwpy.time import to_gps

from . import (const, __version__)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def create_parser(**kwargs):
    """Create a new `argparse.ArgumentParser`
    """
    version = kwargs.pop('version', __version__)
    parser = argparse.ArgumentParser(**kwargs)
    if version is not None:
        add_version_option(parser, version=version)
    return parser


def add_version_option(parser, version=None):
    if version is None:
        version = __version__
    return parser.add_argument('-V', '--version', action='version',
                               version=version)


def add_ifo_option(parser, ifo=const.IFO, required=None):
    """Add a `-i/--ifo` option to the given parser
    """
    if required is None:
        required = const.IFO is None
    return parser.add_argument(
        '-i', '--ifo', default=const.IFO, required=required,
        help='IFO prefix for this analysis, default: %(default)s')


def add_gps_start_stop_arguments(parser, type=to_gps, **kwargs):
    """Add `gpsstart` and `gpsend` arguments to the given parser
    """
    a = parser.add_argument('gpsstart', type=to_gps,
                            help='GPS start time or datetime of analysis',
                            **kwargs)
    b = parser.add_argument('gpsend', type=to_gps,
                            help='GPS end time or datetime of analysis',
                            **kwargs)
    return a, b


def add_gps_start_stop_options(parser, type=to_gps, **kwargs):
    """Add `-s/--gps-start-time` and `-e/--gps-end-time` arguments
    """
    a = parser.add_argument('-s', '--gps-start-time', type=to_gps,
                            help='GPS start time or datetime of analysis',
                            **kwargs)
    b = parser.add_argument('-e', '--gps-end-time', type=to_gps,
                            help='GPS end time or datetime of analysis',
                            **kwargs)
    return a, b


def add_frametype_option(parser, **kwargs):
    """Add a `-f/--frametype` option to this given parser
    """
    kwargs.setdefault('help', 'the frame type name')
    return parser.add_argument('-f', '--frametype', **kwargs)


def add_nproc_option(
        parser, default=8, type=int,
        help='the number of processes to use when reading data, '
             'default: %(default)s',
        **kwargs):
    return parser.add_argument('-j', '--nproc', default=default, help=help,
                               type=type, **kwargs)
