#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) Duncan Macleod (2018)
#
# This file is part of the GWDetChar package.
#
# GWDetChar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWDetChar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWDetChar.  If not, see <http://www.gnu.org/licenses/>.

"""Setup utilities for GWDetChar
"""

import glob
import os.path
from distutils import log

from setuptools import Command
from setuptools.command.egg_info import egg_info
from setuptools.command.build_py import build_py

import versioneer

# import versioneer's modified commands
CMDCLASS = versioneer.get_cmdclass()

# specify HTML source files
SOURCE_FILES = glob.glob(
    os.path.join('gwbootstrap', 'lib', 'gwbootstrap.min.*'))

if not SOURCE_FILES:  # make sure submodule is not empty
    raise ValueError('gwbootstrap submodule is empty, please populate it '
                     'with `git submodule update --init`')


# -- custom commands ----------------------------------------------------------

class BuildHtmlFiles(Command):
    """Grab compiled CSS and minified JavaScript
    """
    description = 'Grab compiled CSS and minified JS'

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @property
    def staticdir(self):
        try:
            return self._static
        except AttributeError:
            self._static = os.path.join(self.distribution.get_name(),
                                        '_static')
            if not os.path.isdir(self._static):
                os.makedirs(self._static)
                log.info('created static dir in %s' % self._static)
        return self._static

    @property
    def staticpackage(self):
        return self.staticdir.replace(os.path.sep, '.')

    def build_utils(self):
        log.info('copying minified elements')
        for file_ in SOURCE_FILES:
            filename = os.path.basename(file_)
            target = os.path.join(self.staticdir, filename)
            copyfile(file_, target)
            log.info('minified CSS and JS written to %s' % target)

    def run(self):
        self.build_utils()
        if self.staticpackage not in self.distribution.packages:
            self.distribution.packages.append(self.staticpackage)
            log.info("added %s to package list" % self.staticpackage)


old_build_py = CMDCLASS.pop('build_py', build_py)


class BuildPyWithHtmlFiles(old_build_py):
    """Custom build_py that grabs compiled CSS+JS sources as well
    """
    def run(self):
        self.run_command('build_html_files')
        old_build_py.run(self)


old_egg_info = CMDCLASS.pop('egg_info', egg_info)


class EggInfoWithHtmlFiles(old_egg_info):
    """Custom egg_info that grabs compiled CSS+JS sources as well
    """
    def run(self):
        self.run_command('build_html_files')
        old_egg_info.run(self)


# update commands
CMDCLASS.update({
    'build_html_files': BuildHtmlFiles,
    'build_py': BuildPyWithHtmlFiles,
    'egg_info': EggInfoWithHtmlFiles,
})
