# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Append a new `VetoDef` entry to an existing veto definer file
"""

import os
import re
import shutil
import tempfile
import argparse

from igwn_ligolw.ligolw import LIGOLWContentHandler
from igwn_ligolw.utils import (load_filename, write_filename, process)
from igwn_ligolw.lsctables import (VetoDefTable, use_in)
from gwpy.segments import DataQualityFlag
from dqsegdb2.utils import get_default_host

from . import validate
from .. import __version__ as ver

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


class LVVetoDefContentHandler(LIGOLWContentHandler):
    pass


use_in(LVVetoDefContentHandler)

FLAG_RE = re.compile(r'\A(?P<ifo>[A-Z]\d):'
                     r'(?P<name>[A-Z-]+[A-Z0-9_]+):'
                     r'(?P<version>\d+)\Z')

DEFAULT_SEGMENT_SERVER = get_default_host()


def main(args=None):

    # -- parse command line ---------------------------------------------------

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=ver)
    parser.add_argument('veto-definer-file', type=str,
                        help='path of veto definer file')
    parser.add_argument('--force', action='store_true', default=False,
                        help='force append, even if data are missing, '
                             'default: %(default)s')
    parser.add_argument('--use-database-metadata', action='store_true',
                        default=False,
                        help='when this option is given, the values for '
                             '--start-time and --end-time will be taken from '
                             'the segment database query; providing --comment '
                             'will override the segment database description')
    parser.add_argument('--skip-process-tables', action='store_true',
                        default=False,
                        help='skip updating proces/process_params '
                             'tables, default: %(default)s')
    vdargs = parser.add_argument_group('VetoDef params')
    vdargs.add_argument('flag', type=str,
                        help='name of flag to append, must take the form '
                             '<ifo>:<name>:<version>, e.g. '
                             'H1:DMT-VETO_FLAG:1')
    vdargs.add_argument('--category', default=1, type=int,
                        help='category for this new flag, '
                             'default: %(default)s')
    vdargs.add_argument('--start-time', default=0, type=int,
                        help='start_time, for this new flag, '
                             'default: %(default)s')
    vdargs.add_argument('--end-time', default=0, type=int,
                        help='end_time, for this new flag, '
                             'default: %(default)s')
    vdargs.add_argument('--start_pad', default=0, type=int,
                        help='start_pad, for this new flag, '
                             'default: %(default)s')
    vdargs.add_argument('--end_pad', default=0, type=int,
                        help='end_pad, for this new flag, '
                             'default: %(default)s')
    vdargs.add_argument('--comment',
                        help='comment for this flag, a short '
                             'description of why this flag is '
                             'relevant for the given search')
    parser.add_argument('-t', '--segment-url',
                        default=DEFAULT_SEGMENT_SERVER,
                        help='URL of segment server, default: %(default)s')

    args = parser.parse_args(args=args)
    vdf = getattr(args, 'veto-definer-file')
    if (not args.force and
            not args.use_database_metadata and
            args.comment is None):
        parser.error("Insert --comment must be given")
    if not args.segment_url and (not args.force or args.use_database_metadata):
        parser.error("--segment-url must be given [DEFAULT_SEGMENT_SERVER "
                     "variable not populated]")

    try:
        match = FLAG_RE.match(args.flag).groupdict()
    except AttributeError as e:
        e.args = (f"Failed to parse {args.flag} as <ifo>:<name>:<version>",)
        raise

    # -- query SEGDB for flag information -------------------------------------
    if args.use_database_metadata:
        query_start = args.start_time if args.start_time else 1
        query_end = args.end_time if args.end_time else 1e10

        metadata = DataQualityFlag.query(
            args.flag,
            query_start,
            query_end,
            host=args.segment_url,
        )

        if not len(metadata.known):
            raise RuntimeError(
                "No known segments were found for the provided flag"
            )

        args.start_time = metadata.known[0][0]
        args.end_time = metadata.known[-1][-1]

        if not args.comment:
            args.comment = metadata.description

    # -- append veto definer entry --------------------------------------------

    # read veto definer file
    xmldoc = load_filename(vdf, contenthandler=LVVetoDefContentHandler)
    table = VetoDefTable.get_table(xmldoc)

    # get process and add process_params
    if args.skip_process_tables:
        pid = None
    else:
        params = vars(args).copy()
        params.pop('force')
        proc = process.register_to_xmldoc(xmldoc,
                                          program=os.path.basename(__file__),
                                          paramdict=params,
                                          version=ver)
        pid = proc.process_id

    # create new veto def
    new = table.RowType()
    new.process_id = pid
    new.ifo = match['ifo']
    new.name = match['name']
    new.version = int(match['version'])
    new.category = args.category
    new.start_time = args.start_time
    new.end_time = args.end_time
    new.start_pad = args.start_pad
    new.end_pad = args.end_pad
    new.comment = args.comment
    table.append(new)

    if not args.force:
        for test in validate.VETO_TESTS:
            if test == validate.check_veto_def_exists:
                test(new, host=args.segment_url)
            else:
                test(new)
        for test in validate.TABLE_TESTS:
            test(table)

    # -- write file (with temporary backup) -----------------------------------

    fd, fn = tempfile.mkstemp(prefix=f'{os.path.basename(__file__)}-',
                              suffix=os.path.splitext(vdf)[1])
    shutil.copy(vdf, fn)
    try:
        write_filename(xmldoc, vdf)
    except Exception:
        shutil.move(fn, vdf)
        raise
    else:
        os.remove(fn)


if __name__ == "__main__":
    main()
