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

from getpass import getuser
from distutils.spawn import find_executable
from pycondor import (Dagman, Job)

from .. import condor

__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# set default accounting information
ACCOUNTING_GROUP = os.getenv(
    '_CONDOR_ACCOUNTING_GROUP', 'ligo.dev.{epoch}.detchar.user_req.omegascan')
ACCOUNTING_GROUP_USER = os.getenv(
    '_CONDOR_ACCOUNTING_USER', getuser())


# -- utilities ----------------------------------------------------------------

def get_command_line_flags(ifo, colormap='viridis', nproc=8, far=3.171e-8,
                           config_file=None, disable_correlation=False,
                           disable_checkpoint=False, ignore_state_flags=False):
    """Get a list of optional command-line arguments to `gwdetchar-omega`
    """
    flags = [
        "--ifo", ifo,
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
        a list of command line flags to run for each job, defaults to an
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
    executable = find_executable('gwdetchar-omega')
    # create DAG and jobs
    dagman = Dagman(name=tag, submit=subdir)
    job = Job(
        dag=dagman,
        name=os.path.basename(executable),
        executable=executable,
        universe=universe,
        submit=subdir,
        error=logdir,
        output=logdir,
        getenv=True,
        request_memory=4096 if universe != "local" else None,
        extra_lines=condor_commands
    )
    # make a node in the workflow for each event time
    for t in times:
        cmd = " ".join([str(t)] + [
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
