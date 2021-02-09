# coding=utf-8
# Copyright (C) Alex Urban (2019)
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

"""Batch-mode utilities for omega scans
"""

import os
import subprocess
import sys

from getpass import getuser
from pycondor import (Dagman, Job)

from .. import (cli, condor)

# authorship credits
__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# set CLI docstring
CLI_DOCSTRING = """Batch-generate a series of Omega scans

GPS times can be given individually on the command-line, one after the other,
or can be bundled into one file formatted where the first column contains
the GPS times (other columns are ignored).

The output of this script is a condor workflow in the form of a DAG file,
with associated condor submit (`.sub`) file in the output directory.
Submitting the workflow to Condor will result in the scans being processed
in parallel.
"""

# set default accounting information
ACCOUNTING_GROUP = os.getenv(
    '_CONDOR_ACCOUNTING_GROUP',
    'ligo.dev.{epoch}.detchar.user_req.omegascan',
)
ACCOUNTING_GROUP_USER = os.getenv(
    '_CONDOR_ACCOUNTING_USER',
    getuser(),
)

# set program name
PROG = ('python -m gwdetchar.omega.batch' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))


# -- utilities ----------------------------------------------------------------

def _monitor_dag_workflow(dagman):
    """Monitor a batch of Omega scans through the Condor pool
    """
    print("Monitoring progress of {0.submit_file}".format(dagman))
    try:
        subprocess.check_call(
            ["pycondor", "monitor", dagman.submit_file],
        )
    except KeyboardInterrupt:
        pass


def _parse_analysis_times(tlist):
    """Parse an iterable of GPS time data for a batch of Omega scans
    """
    if len(tlist) == 1:
        try:  # try converting to GPS
            tlist = [float(tlist[0])]
        except (TypeError, ValueError):  # otherwise read as file
            import numpy
            tlist = numpy.loadtxt(tlist[0], dtype=float, ndmin=1)
    else:
        tlist = list(map(float, tlist))
    return tlist


def get_command_line_flags(ifo, fscale='log', colormap='viridis', nproc=8,
                           far=3.171e-8, config_file=None,
                           disable_correlation=False, disable_checkpoint=False,
                           ignore_state_flags=False):
    """Get a list of optional command-line arguments to `gwdetchar-omega`
    """
    flags = [
        "--ifo", ifo,
        "--frequency-scaling", fscale,
        "--colormap", colormap,
        "--nproc", str(nproc),
        "--far-threshold", str(far),
    ]
    if config_file is not None:
        flags.extend(("--config-file", os.path.abspath(config_file)))
    if disable_correlation:
        flags.append("--disable-correlation")
    if disable_checkpoint:
        flags.append("--disable-checkpoint")
    if ignore_state_flags:
        flags.append("--ignore-state-flags")
    return flags


def get_condor_arguments(accounting_group=ACCOUNTING_GROUP,
                         accounting_group_user=ACCOUNTING_GROUP_USER,
                         timeout=0, extra_commands=[], gps=0):
    """Get a list of arguments for Condor processing
    """
    # get reference epoch
    if '{epoch}' in accounting_group:
        epoch = condor.accounting_epoch(gps)
        accounting_group = accounting_group.format(epoch=epoch.lower())
    # validate accounting tag
    condor.is_valid(accounting_group)
    # determine condor arguments
    condorcmds = [
        "accounting_group = {}".format(accounting_group),
        "accounting_group_user = {}".format(accounting_group_user),
    ]
    if timeout:
        condorcmds.append("periodic_remove = {}".format(
            'CurrentTime-EnteredCurrentStatus > {}'.format(
                3600 * timeout),
        ))
    condorcmds.extend(extra_commands)
    return condorcmds


def generate_dag(times, flags=[], tag='gwdetchar-omega-batch',
                 submit=False, outdir=os.getcwd(), universe='vanilla',
                 condor_commands=get_condor_arguments()):
    """Construct a Directed Acyclic Graph (DAG) for a batch of omega scans

    Parameters
    ----------
    times : `list` of `float`
        list of GPS times to scan

    flags : `list` of `str`, optional
        a list of command-line flags to run for each job, defaults to an
        empty list

    tag : `str`, optional
        a helpful string to use to name the DAG,
        default: `'gwdetchar-omega-batch'`

    submit : `bool`, optional
        submit the DAG to condor, default: `False`

    outdir : `str`, optional
        the output directory in which to store files, will result in
        sub-directories called `'condor'` and `'log'`, default: `os.getcwd`

    universe : `str`, optional
        condor universe to run in, default: `'vanilla'`

    condor_commands : `list` of `str`, optional
        list of condor settings to process with, defaults to the output of
        `get_condor_arguments`

    Returns
    -------
    dagman : `~pycondor.Dagman`
        the fully built DAG object
    """
    logdir = os.path.join(outdir, 'logs')
    subdir = os.path.join(outdir, 'condor')
    # create DAG and jobs
    dagman = Dagman(name=tag, submit=subdir)
    job = Job(
        dag=dagman,
        name='gwdetchar-omega',
        executable=sys.executable,
        universe=universe,
        submit=subdir,
        error=logdir,
        output=logdir,
        getenv=True,
        request_memory=4096 if universe != "local" else None,
        extra_lines=condor_commands,
    )
    # make a node in the workflow for each event time
    for t in times:
        cmd = " ".join(["-m", "gwdetchar.omega", str(t)] + [
            "--output-directory", os.path.join(outdir, str(t))] + flags)
        job.add_arg(cmd, name=str(t).replace(".", "_"))
    # write and submit the DAG
    dagman.build(fancyname=False)
    print("Workflow generated for {} times".format(len(times)))
    if submit:
        dagman.submit_dag(submit_options="-force")
        print(
            "Submitted to condor, check status via:\n\n"
            "$ condor_q {}".format(getuser())
        )
    else:
        print(
            "Submit to condor via:\n\n"
            "$ condor_submit_dag {0.submit_file}".format(dagman),
        )
    return dagman


# -- parse command-line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize argument parser
    parser = cli.create_parser(
        prog=PROG,
        description=CLI_DOCSTRING,
    )
    pargs = parser.add_argument_group('Omega scan options')
    cargs = parser.add_argument_group('Condor options')

    # required arguments
    parser.add_argument(
        'gpstime',
        nargs='+',
        help='GPS time(s) to scan, or path to a file'
             'containing a single column of such times',
    )
    cli.add_ifo_option(
        parser,
    )
    parser.add_argument(
        '-o',
        '--output-dir',
        default=os.getcwd(),
        help='output directory for all scans, default: %(default)s',
    )

    # optional omega scan arguments
    pargs.add_argument(
        '-f',
        '--config-file',
        help='path to configuration file to use, default: '
             'choose based on observatory, epoch, and pipeline',
    )
    pargs.add_argument(
        '-d',
        '--disable-correlation',
        action='store_true',
        default=False,
        help='disable cross-correlation of aux '
             'channels, default: False',
    )
    pargs.add_argument(
        '-D',
        '--disable-checkpoint',
        action='store_true',
        default=False,
        help='disable checkpointing from previous '
             'runs, default: False',
    )
    pargs.add_argument(
        '-s',
        '--ignore-state-flags',
        action='store_true',
        default=False,
        help='ignore state flag definitions in '
             'the configuration, default: False',
    )
    pargs.add_argument(
        '-t',
        '--far-threshold',
        type=float,
        default=3.171e-8,
        help='white noise false alarm rate threshold (Hz) for '
             'processing channels, default: %(default)s',
    )
    pargs.add_argument(
        '-y',
        '--frequency-scaling',
        default='log',
        help='scaling of all frequency axes, default: %(default)s',
    )
    pargs.add_argument(
        '-c',
        '--colormap',
        default='viridis',
        help='name of colormap to use, default: %(default)s',
    )
    cli.add_nproc_option(
        pargs,
    )

    # optional condor arguments
    cargs.add_argument(
        '-u',
        '--universe',
        default='vanilla',
        type=str,
        help='universe for condor processing',
    )
    cargs.add_argument(
        '--submit',
        action='store_true',
        default=False,
        help='submit DAG directly to condor queue',
    )
    cargs.add_argument(
        '--monitor',
        action='store_true',
        default=False,
        help='monitor the DAG progress after submission; '
             'only used with --submit',
    )
    cargs.add_argument(
        '--condor-accounting-group',
        default=ACCOUNTING_GROUP,
        help='accounting_group for condor submission on the LIGO '
             'Data Grid, include \'{epoch}\' (with curly brackets) '
             'to auto-substitute the appropriate epoch based on '
             'the GPS times',
    )
    cargs.add_argument(
        '--condor-accounting-group-user',
        default=ACCOUNTING_GROUP_USER,
        help='accounting_group_user for condor submission on the '
             'LIGO Data Grid',
    )
    cargs.add_argument(
        '--condor-timeout',
        type=float,
        default=None,
        metavar='T',
        help='configure condor to terminate jobs after T hours '
             'to prevent idling, default: %(default)s',
    )
    cargs.add_argument(
        '--condor-command',
        action='append',
        default=[],
        help='Extra condor submit commands to add to '
             'gw_summary submit file. Can be given '
             'multiple times in the form "key=value"',
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the command-line Omega scan tool in batch mode
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # set up output directory
    outdir = os.path.abspath(
        os.path.expanduser(args.output_dir))

    # parse analysis times
    times = _parse_analysis_times(
        getattr(args, 'gpstime'))

    # get condor arguments
    condorcmds = get_condor_arguments(
        accounting_group=args.condor_accounting_group,
        accounting_group_user=args.condor_accounting_group_user,
        timeout=args.condor_timeout,
        extra_commands=args.condor_command,
        gps=max(times),
    )

    # get command-line flags
    flags = get_command_line_flags(
        args.ifo,
        fscale=args.frequency_scaling,
        colormap=args.colormap,
        nproc=args.nproc,
        far=args.far_threshold,
        config_file=args.config_file,
        disable_correlation=args.disable_correlation,
        disable_checkpoint=args.disable_checkpoint,
        ignore_state_flags=args.ignore_state_flags,
    )

    # -- generate workflow ------------

    # write and submit the DAG
    dagman = generate_dag(
        times,
        flags=flags,
        tag="gwdetchar-omega-batch",
        submit=args.submit,
        outdir=outdir,
        universe=args.universe,
        condor_commands=condorcmds,
    )

    # monitor DAG progress
    if (args.submit and args.monitor):
        _monitor_dag_workflow(dagman)


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
