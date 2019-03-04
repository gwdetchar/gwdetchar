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
JS_FILES = [
    f for f in glob.glob(os.path.join('share', 'js', '*.js')) + (
               glob.glob(os.path.join('bootstrap-ligo', 'js', '*.js')))
    if not f.endswith('.min.js')]
SASS_FILES = glob.glob(os.path.join('share', 'sass', '[!_]*.scss')) + (
    glob.glob(os.path.join('bootstrap-ligo', 'css', '[!_]*.scss')))

# make sure submodule is not empty
static = glob.glob(os.path.join('bootstrap-ligo', '*'))
if not static:
    raise ValueError('bootstrap-ligo submodule is empty, please populate it '
                     'with `git submodule update --init`')


# -- custom commands ----------------------------------------------------------

class BuildHtmlFiles(Command):
    """Compile SASS sources into CSS and minify javascript
    """
    description = 'Compile SASS into CSS and minify JS'
    user_options = [
        ('output-style=', None, 'CSS output style'),
    ]

    def initialize_options(self):
        self.output_style = 'compressed'

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

    def build_js(self):
        jsdir = os.path.join('share', 'js')
        log.info('minifying js under %s' % jsdir)
        for jsfile in JS_FILES:
            filename = os.path.basename(jsfile)
            target = os.path.join(
                self.staticdir, '%s.min.js' % os.path.splitext(filename)[0])
            self.minify_js(jsfile, target)
            log.info('minified js written to %s' % target)

    @staticmethod
    def minify_js(source, target):
        import jsmin
        js = jsmin.jsmin(open(source).read())
        with open(target, 'w') as f:
            f.write(js)

    def build_css(self):
        sassdir = os.path.join('share', 'sass')
        log.info('compiling SASS under %s to CSS' % sassdir)
        for sassfile in SASS_FILES:
            filename = os.path.basename(sassfile)
            target = os.path.join(
                self.staticdir, '%s.min.css' % os.path.splitext(filename)[0])
            self.compile_sass(sassfile, target, output_style=self.output_style)
            log.info('%s CSS written to %s' % (self.output_style, target))

    @staticmethod
    def compile_sass(source, target, **kwargs):
        import sass
        css = sass.compile(filename=source, **kwargs)
        with open(target, 'w') as f:
            f.write(css)

    def run(self):
        self.build_css()
        self.build_js()
        if self.staticpackage not in self.distribution.packages:
            self.distribution.packages.append(self.staticpackage)
            log.info("added %s to package list" % self.staticpackage)


old_build_py = CMDCLASS.pop('build_py', build_py)


class BuildPyWithHtmlFiles(old_build_py):
    """Custom build_py that compiles SASS+JS sources as well
    """
    def run(self):
        self.run_command('build_html_files')
        old_build_py.run(self)


old_egg_info = CMDCLASS.pop('egg_info', egg_info)


class EggInfoWithHtmlFiles(old_egg_info):
    """Custom egg_info that compiles SASS+JS sources as well
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
