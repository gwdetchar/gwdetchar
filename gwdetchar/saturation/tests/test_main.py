# -*- coding: utf-8 -*-
# Copyright (C) Luca Cirfeta (2026)
#
# This file is part of the GW DetChar python package.
#
# gwdetchar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwdetchar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwdetchar.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for the :mod:`gwdetchar.saturation` command-line interface."""

from unittest import mock

import pytest

from gwpy.segments import DataQualityFlag

from .. import __main__ as saturation_cli


ALL_CHANNELS = [
    "X1:KEEP_LIMIT",
    "X1:KEEP_LIMEN",
    "X1:DROP_LIMIT",
    "X1:DROP_LIMEN",
    "X1:KEEP-SWSTAT_LIMIT",
    "X1:KEEP-SWSTAT_SWSTAT",
    "X1:DROP-SWSTAT_LIMIT",
    "X1:DROP-SWSTAT_SWSTAT",
]


@mock.patch.object(saturation_cli.DataQualityDict, "write")
@mock.patch.object(saturation_cli.core, "is_saturated")
@mock.patch.object(
    saturation_cli,
    "get_channel_names",
    return_value=ALL_CHANNELS,
)
@mock.patch.object(
    saturation_cli.gwdatafind,
    "find_urls",
    return_value=["X-TEST-0-1.gwf"],
)
@pytest.mark.parametrize(("requested", "expected"), [
    (
        None,
        [
            ["X1:DROP", "X1:KEEP"],
            ["X1:DROP-SWSTAT", "X1:KEEP-SWSTAT"],
        ],
    ),
    (
        "X1:KEEP\nX1:KEEP-SWSTAT\nX1:MISSING\n",
        [["X1:KEEP"], ["X1:KEEP-SWSTAT"]],
    ),
    ("X1:KEEP\n", [["X1:KEEP"]]),
])
def test_main_channel_selection(
    find_urls,
    get_channel_names,
    is_saturated,
    write,
    monkeypatch,
    tmp_path,
    requested,
    expected,
):
    """``--channels`` should restrict the default channel selection."""
    is_saturated.side_effect = lambda channels, *args, **kwargs: [
        DataQualityFlag(name=channel) for channel in channels
    ]
    monkeypatch.setenv("LIGO_DATAFIND_SERVER", "datafind.example")
    monkeypatch.chdir(tmp_path)

    args = [
        "0",
        "1",
        "--ifo",
        "X1",
        "--frametype",
        "X1_R",
    ]
    if requested is not None:
        channels = tmp_path / "channels.txt"
        channels.write_text(requested)
        args.extend(["--channels", str(channels)])

    saturation_cli.main(args)

    assert is_saturated.call_count == len(expected)
    assert [call.args[0] for call in is_saturated.call_args_list] == expected
