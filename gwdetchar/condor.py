# coding=utf-8
# Copyright (C) Duncan Macleod (2018)
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

"""HTCondor utilities for `gwdetchar`
"""

import json
import re

from . import const

OBS_RUN_REGEX = re.compile('[OS][0-9]*', re.I)
ACCOUNTING_GROUPS_FILE = '/etc/condor/accounting_groups.json'


def accounting_epoch(gpstime):
    """Return the appropriate epoch for condor accounting tags

    Examples
    --------
    >>> from gwdetchar.condor import accounting_epoch
    >>> print(accounting_epoch(1126259462))  # GW150914
    'O1'
    """
    for epoch in filter(OBS_RUN_REGEX.match, const.EPOCH):
        # if gpstime falls before the _end_ of this run, use it
        if float(gpstime) < const.EPOCH[epoch][1]:
            return epoch
    # gpstime falls _after_ the end of the last known epoch, use it
    return epoch


def is_valid(tag, path=ACCOUNTING_GROUPS_FILE):
    """Determine whether an accounting tag is valid, and raise an exception
    if not
    """
    try:
        valid = validate_accounting_tag(tag, path=path)
    except EnvironmentError:
        valid = True  # failed to load condor tags, not important
    if not valid:
        listtags = 'cat {0} | json_pp | less'.format(path)
        raise ValueError("condor accounting tag {0!r} not recognised, to see "
                         "the list of valid groups, please run `{1}`".format(
                             tag, listtags))
    return valid


def validate_accounting_tag(tag, path=ACCOUNTING_GROUPS_FILE):
    """Validate a given accounting tag

    This loads the list of known accounting tags from ``path`` and
    checks for ``tag`` in that list.

    Returns
    -------
    True
        if ``tag`` is found in the list of tags
    False
        if ``tag`` is **not** found in the list of tags
    """
    return tag in load_accounting_tags(path=path)


def load_accounting_tags(path=ACCOUNTING_GROUPS_FILE):
    """Load the list of known accounting tags
    """
    with open(path, 'r') as fobj:
        return json.load(fobj)['groups']
