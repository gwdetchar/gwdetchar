# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Evan Goetz (2025)
#
# This file is part of gwdetchar

"""Create an empty veto-definer file
"""

import os.path
import argparse

from lal.utils import CacheEntry
from igwn_ligolw.ligolw import (Document, LIGO_LW)
from igwn_ligolw.lsctables import (New, VetoDefTable)
from igwn_ligolw.utils import (write_filename, process)

from .. import __version__ as ver

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def main(args=None):

    # -- parse command line ---------------------------------------------------

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=ver)
    parser.add_argument('output-file', type=str,
                        help='output filename for veto definer')
    parser.add_argument('--force', action='store_true', default=False,
                        help='disable file-name validation, '
                             'default: %(default)s')
    parser.add_argument('--ifos', type=str, required=True,
                        help='comma-separated list of IFO prefixes')
    parser.add_argument('--skip-process-tables', action='store_true',
                        default=False,
                        help='skip updating proces/process_params tables, '
                             'default: %(default)s')

    args = parser.parse_args(args=args)
    outfile = getattr(args, 'output-file')

    # verify sensible filename
    if not args.force and not outfile.endswith(('.xml', '.xml.gz')):
        raise ValueError(
            "Output filename must carry a `.xml` or `.xml.gz` extension"
        )
    elif not args.force:
        try:
            CacheEntry.from_T050017(outfile)
        except ValueError as e:
            e.args = ('Output filename must follow the T050017 convention '
                      '[https://dcc.ligo.org/LIGO-T050017]',)
            raise

    # -- create document ------------------------------------------------------

    xmldoc = Document()
    xmldoc.appendChild(LIGO_LW())

    # append process and process_params
    if not args.skip_process_tables:
        params = vars(args).copy()
        params.pop('force')
        _ = process.register_to_xmldoc(
            xmldoc,
            program=os.path.basename(__file__),
            paramdict=params,
            version=ver,
        )

    # add veto definer table
    xmldoc.childNodes[-1].appendChild(New(VetoDefTable))

    # write
    write_filename(xmldoc, outfile)


if __name__ == "__main__":
    main()
