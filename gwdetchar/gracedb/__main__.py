# coding=utf-8
# Copyright (C) Evan Goetz (2025)
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

"""Custom summary page to display events queried from the Gravitational-wave
Candidate Event Database (GraceDb)
"""

import os
import sys

from .. import cli
from .gracedb import GraceDb
from ..utils import get_states

PROG = ('python -m gwdetchar.lasso' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


# -- parse command-line -------------------------------------------------------

def create_parser():
    parser = cli.create_parser(
        prog=PROG,
        description=__doc__,
        formatter_class=cli.argparse.ArgumentDefaultsHelpFormatter,
    )

    cli.add_gps_start_stop_options(parser, required=True)

    parser.add_argument(
        '-q',
        '--query',
        type=str,
        default='External',
        help='Query string',
    )
    parser.add_argument(
        '-S',
        '--states',
        type=str,
        default=(
            'All,'
            'H1:DMT-ANALYSIS_READY:1&L1:DMT-ANALYSIS_READY:1,'
            'H1:DMT-ANALYSIS_READY:1&L1:DMT-ANALYSIS_READY:1!'
            'H1:DMT-INJECTION_TRANSIENT:1!L1:DMT-INJECTION_TRANSIENT:1'),
        help='Comma separated string of IFO states',
    )
    parser.add_argument(
        '-n',
        '--state-names',
        type=str,
        default='All,H1-L1 obs.,No HWinj',
        help='Comma separated string for the names of the states',
    )
    parser.add_argument(
        '-c',
        '--columns',
        type=str,
        default='graceid,gpstime,date,pipeline,search,ra,dec,error_radius',
        help='Comma separated string of columns in this webpage instance',
    )
    parser.add_argument(
        '-H',
        '--headers',
        type=str,
        default='ID,GPS time,UTC time,Source,Type,RA,Dec.,Error radius',
        help=('Comma separated string of column labels in this webpage '
              'instance'),
    )
    parser.add_argument(
        '-r',
        '--rank',
        type=str,
        default=None,
        help='Ranking scheme',
    )
    parser.add_argument(
        '-o',
        '--output-path',
        type=str,
        required=True,
        help='Output path',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help='log verbose output, default: %(default)s',
    )

    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args=args)

    # set up logger
    logger = cli.logger(
        name=PROG.split('python -m ').pop(),
        level='DEBUG' if args.verbose else 'INFO',
    )

    # get states
    logger.info("Getting states")
    dqdict = get_states(
        args.states,
        args.state_names,
        args.gps_start_time,
        args.gps_end_time,
    )

    grace_db = GraceDb(
        'test',
        args.gps_start_time,
        args.gps_end_time,
    )

    # query GraceDB
    logger.info("Querying GraceDB")
    grace_db.process()

    # process states and make HTML
    for state in dqdict:
        logger.info(f"Processing state {state}")
        grace_db.process_state(dqdict[state])
        grace_db.write_state_html(dqdict[state], args.output_path)

    logger.info("Done")


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
