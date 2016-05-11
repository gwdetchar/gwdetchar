# -*- coding: utf-8 -*-
# Copyright (C) Joshua Smith (2016-)
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

"""Test suite for `gwdetchar.cli`
"""

import argparse

from gwdetchar import cli

from common import unittest


class CliTestCase(unittest.TestCase):
    def test_create_parser(self):
        parser = cli.create_parser(description=__doc__)
        self.assertIsInstance(parser, argparse.ArgumentParser)
        self.assertEqual(parser.description, __doc__)
