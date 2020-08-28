# -*- coding: utf-8 -*-
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
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for `gwdetchar.omega.batch`
"""

import os
import pytest
import shutil
import numpy.testing as nptest

from getpass import getuser
from pycondor import Dagman
from unittest import mock

from .. import batch

__author__ = 'Alex Urban <alexander.urban@ligo.org>'

# global test objects

FLAGS = [
    '--ifo', 'X1',
    '--frequency-scaling', 'log',
    '--colormap', 'viridis',
    '--nproc', '8',
    '--far-threshold', '3.171e-08',
    '--disable-correlation',
    '--disable-checkpoint',
    '--ignore-state-flags',
]

CONDORCMDS = [
    'accounting_group = ligo.dev.o1.detchar.user_req.omegascan',
    'accounting_group_user = {}'.format(getuser()),
    'periodic_remove = CurrentTime-EnteredCurrentStatus > 14400',
    'test',
]


# -- unit tests ---------------------------------------------------------------

def test_get_command_line_flags():
    ifo = 'X1'
    flags = batch.get_command_line_flags(
        ifo, disable_correlation=True, disable_checkpoint=True,
        ignore_state_flags=True)
    nptest.assert_array_equal(flags, FLAGS)


def test_get_condor_arguments():
    gps = 1126259462
    condorcmds = batch.get_condor_arguments(
        timeout=4, extra_commands=['test'], gps=gps)
    nptest.assert_array_equal(condorcmds, CONDORCMDS)


@mock.patch('pycondor.Dagman.submit_dag', return_value=None)
def test_generate_dag(dag, tmpdir, capsys):
    outdir = str(tmpdir)
    times = [1187008882]
    # test without submit
    dagman = batch.generate_dag(
        times, flags=FLAGS, outdir=outdir, condor_commands=CONDORCMDS)
    assert isinstance(dagman, Dagman)
    assert os.listdir(os.path.join(outdir, 'condor'))
    assert os.path.isdir(os.path.join(outdir, 'logs'))
    (out, err) = capsys.readouterr()
    assert not err
    assert out.startswith('The directory')
    assert 'Submit to condor via' in out
    # test with submit
    dagman = batch.generate_dag(
        times, flags=FLAGS, submit=True, outdir=outdir,
        condor_commands=CONDORCMDS)
    (out, err) = capsys.readouterr()
    assert not err
    assert 'condor_q' in out
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)


# -- cli tests ----------------------------------------------------------------

@pytest.mark.parametrize('args', (
    ['1126259462.4', '--ifo', 'H1'],
    ['1128678900.4', '1135136350.6', '--submit', '--ifo', 'L1'],
    ['event-times.txt', '--submit', '--monitor', '--ifo', 'Network'],
))
@mock.patch('numpy.loadtxt', return_value=[
    1167559936.6, 1180922494.5, 1185389807.3])
@mock.patch('pycondor.Dagman.submit_dag', return_value=None)
@mock.patch('subprocess.check_call', return_value=None)
def test_main(subp, dag, loadtxt, args, tmpdir):
    outdir = str(tmpdir)
    batch.main(args + ['--output-dir', outdir])
    # test output
    assert os.listdir(os.path.join(outdir, 'condor'))
    assert os.path.isdir(os.path.join(outdir, 'logs'))
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
