# coding=utf-8
# Copyright (C) Duncan Macleod (2019)
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

"""Pytest configuration for GWDetChar
"""

import os
from unittest import mock

import pytest


def fake_package_list():
    """Fake return for `gwdetchar.io.html.package_list`

    The real :func:`package_list` takes a while and doesn't add
    anything to any of the tests, so we should fake it almost all
    of the time.
    """
    return [
        {
            "name": "package1",
            "version": "1.0.0",
            "build_string": "0",
            "channel": "conda-forge",
        },
        {
            "name": "package2",
            "version": "2.0.0",
            "build_string": "1",
            "channel": "conda-forge",
        },
    ]


@pytest.fixture(autouse=True)
def mock_package_list(request):
    """Automatically mock out `gwdetchar.io.html.package_list` in all tests
    """
    # don't apply the mock to functions that test `package_list` itself
    if "package_list" in request.node.name:
        yield
        return
    # mock everything else
    with mock.patch("gwdetchar.io.html.package_list", fake_package_list):
        yield


# -- pytest fixture overrides -------------------------------------------------
# these new fixtures overload the pytest builtin `tmpdir` and `tmp_path`
# to ensure that the session is returned to the starting directory once
# the test has finished (regardless of state).  This is a quick-fix to
# address the fact that many existing tests execute `os.chdir(tmpdir)`
# or similar, then run `shutil.rmtree`, leaving the session with a CWD
# that doesn't exist.

@pytest.fixture
def tmpdir(tmpdir):
    """Overload pytest's `tmpdir` to preserve the CWD from the test start
    """
    start = os.getcwd()
    try:
        yield tmpdir
    finally:
        os.chdir(start)


@pytest.fixture
def tmp_path(tmp_path):
    """Overload pytest's `tmp_path` to preserve the CWD from the test start
    """
    start = os.getcwd()
    try:
        yield tmp_path
    finally:
        os.chdir(start)
