# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Validate a veto definer against all standards
"""

import sys
import argparse
import textwrap

from igwn_ligolw.utils import load_filename
from igwn_ligolw.ligolw import PartialLIGOLWContentHandler
from igwn_ligolw.lsctables import (use_in, VetoDefTable)

from dqsegdb2.utils import get_default_host

from . import validate
from .. import __version__ as ver

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# get fancy colours
RESET_SEQ = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"

# get defaults
VERBOSE = False
DEFAULT_SEGMENT_SERVER = get_default_host()


def sanity_check(test, target, catch=False):
    name = test.__name__
    if isinstance(target, VetoDefTable.RowType):
        name += f" [{target.ifo}:{target.name}:{target.version}]"
    try:
        test(target)
    except AssertionError as e:
        print_status(f"{name}", False)
        if catch:
            if VERBOSE:
                print('\n'.join(textwrap.wrap(
                          str(e), initial_indent=" |  ",
                          subsequent_indent=" |      ")))
            return 1
        else:
            raise
    else:
        print_status("%s" % name, True)
    return 0


def print_status(test, passed=True):
    if passed:
        status = f"{GREEN}Pass{RESET_SEQ}"
    else:
        status = f"{RED}Fail{RESET_SEQ}"
    if VERBOSE:
        print(f"{test}: {status}")


class VetoDefContentHandler(PartialLIGOLWContentHandler):
    @staticmethod
    def _filter(name, attrs):
        return VetoDefTable.CheckProperties(name, attrs)

    def __init__(self, document):
        super(VetoDefContentHandler, self).__init__(document, self._filter)


use_in(VetoDefContentHandler)


def main(args=None):

    # -- parse command line ---------------------------------------------------

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-V', '--version', action='version', version=ver)
    parser.add_argument('veto-definer-file')
    parser.add_argument('-a', '--test-all', action='store_true', default=False,
                        help="perform all tests (default: %(default)s, "
                             "stop after first failure)")
    parser.add_argument('-t', '--segment-url', default=DEFAULT_SEGMENT_SERVER,
                        required=DEFAULT_SEGMENT_SERVER is None,
                        help='URL of segment server (default: %(default)s)')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='print verbose output (default: %(default)s)')
    parser.add_argument('--no-color', default=False, action='store_true',
                        help='print without coloured text')

    args = parser.parse_args(args=args)

    validate.DEFAULT_SEGMENT_SERVER = args.segment_url
    global VERBOSE
    VERBOSE = args.verbose

    vdf = getattr(args, 'veto-definer-file')
    if args.no_color:
        green = red = reset_sq = ''
    else:
        green = GREEN
        red = RED
        reset_sq = RESET_SEQ

    if VERBOSE:
        print('-' * 80)
    print(f"Testing veto-definer file\n\n{vdf}\n")
    if VERBOSE:
        print('-' * 80)

    # load table
    xmldoc = load_filename(vdf, contenthandler=VetoDefContentHandler)
    table = VetoDefTable.get_table(xmldoc)
    table.sort(key=lambda row: (row.ifo, row.name, row.version))
    print_status("LIGO_LW XML parsing", passed=True)

    # -- test table is self-consistent ----------------------------------------

    tablefailed = 0

    if VERBOSE:
        print("\n-- Testing table is self-consistent  "
              "------------------------------------------")
        for test in validate.TABLE_TESTS:
            tablefailed += sanity_check(test, table, catch=args.test_all)

    if tablefailed:
        print(f"{red}Table failed self-consistency tests{reset_sq}")
    else:
        print(f"{green}Table passed self-consistency tests{reset_sq}")

    # -- test flags individually ----------------------------------------------

    if VERBOSE:
        print("\n-- Testing flags individually  "
              "------------------------------------------------")

    vetofailed = []

    for test in validate.VETO_TESTS:
        for veto in table:
            if sanity_check(test, veto, catch=args.test_all):
                vetofailed.append(veto)

    if vetofailed:
        print(f"{red}Some flags don't pass the individual tests{reset_sq}")
        print(" |  %s" % " |  ".join(
            ['%s:%s:%d' % (veto.ifo, veto.name, veto.version) for
             veto in vetofailed]))
    else:
        print(f"{green}All flags pass the individual tests{reset_sq}")

    # print success and exit
    failures = tablefailed + len(vetofailed)
    if VERBOSE:
        print('-' * 80)
    if failures:
        print(f"{red}Failed {failures} tests{reset_sq}")
        sys.exit(1)
    else:
        print(f"{green}All tests passed{reset_sq}")
    if VERBOSE:
        print('-' * 80)


if __name__ == "__main__":
    main()
