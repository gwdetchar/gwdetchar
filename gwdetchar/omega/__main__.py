# coding=utf-8
# Copyright (C) LIGO Scientific Collaboration (2015-)
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

"""Produce an Omega scan for a list of channels around a given GPS time

This utility can be used to process an arbitrary list of detector channels
with minimal effort in finding data. The input should be an INI-formatted
configuration file that lists processing options and channels in contextual
blocks. For more information, see gwdetchar.omega.config.
"""

import numpy
import os
import sys
import warnings

from gwpy.table import Table
from gwpy.time import to_gps

from .. import (cli, omega)
from ..io.datafind import (check_flag, get_data)
from . import (config, html)

from matplotlib import use
use('Agg')

# backend-dependent import
from . import plot  # noqa: E402

# authorship credits
__author__ = 'Alex Urban <alexander.urban@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

# set up logger
PROG = ('python -m gwdetchar.omega' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())


# -- utilities ----------------------------------------------------------------

def _finalize_html(analyzed, ifo, gps, htmlv):
    """Write the final HTML data product for this analysis
    """
    htmlv['refresh'] = False  # turn off auto-refresh
    if analyzed:
        html.write_qscan_page(ifo, gps, analyzed, **htmlv)
        return
    reason = ('No significant channels found '
              'during active analysis segments')
    html.write_null_page(ifo, gps, reason, context=ifo.lower())


def _init_analyzed_channels():
    """Initialize a running, ordered record of analyzed channels
    """
    if sys.version_info >= (3, 7):  # python 3.7+
        return {}
    from collections import OrderedDict
    return OrderedDict()


def _load_channel_record(summary, use_checkpoint=True, correlate=True):
    """Load a previous Omega scan from its last saved checkpoint
    """
    if not (use_checkpoint and os.path.exists(summary)):
        return ([], [])
    LOGGER.debug('Checkpointing from {}'.format(
        os.path.abspath(summary)))
    record = Table.read(summary)
    if correlate and ('Standard Deviation' not in record.colnames):
        raise KeyError(
            'Cross-correlation is not available from this record, '
            'consider running without correlation or starting from '
            'scratch with --disable-checkpoint')
    completed = list(record['Channel'])
    return (record, completed)


def _load_channel_from_checkpoint(block_name, channel, analyzed,
                                  completed, record, correlated):
    """Load channel data from a previous analysis
    """
    LOGGER.info(' -- Checkpointing {} from a previous '
                'run'.format(channel.name))
    cindex = completed.index(channel.name)
    channel.load_loudest_tile_features(
        record[cindex], correlated=correlated)
    return html.update_toc(analyzed, channel, name=block_name)


def _parse_configuration(inifiles, ifo=None, gps=None):
    """Parse configuration files for this Omega scan
    """
    # get path(s) to configuration files
    inifiles = [os.path.abspath(f) for f in (
        inifiles or
        config.get_default_configuration(ifo, gps)
    )]
    # parse configuration files
    LOGGER.debug('Parsing the following configuration files:')
    for fname in inifiles:
        LOGGER.debug(''.join([' -- ', fname]))
    return inifiles


def _scan_channel(channel, data, analyzed, gps, block, fthresh,
                  logf, fscale, colormap, block_name, correlate=None):
    """Perform Omega scan on an individual data channel
    """
    try:  # scan the channel
        LOGGER.info(' -- Scanning channel {}'.format(channel.name))
        series = omega.scan(
            gps, channel, data.astype('float64'), block.fftlength,
            resample=block.resample, fthresh=fthresh, search=block.search,
            logf=logf)
    except (ValueError, KeyError) as exc:
        warnings.warn("Skipping {}: [{}] {}".format(
            channel.name, type(exc), str(exc)), UserWarning)
        return analyzed
    # if channel is insignificant, skip it
    if series is None:
        LOGGER.warning(
            ' -- Channel not significant at white noise false alarm '
            'rate {} Hz'.format(fthresh))
        return analyzed
    # plot Omega scan products
    LOGGER.info(
        ' -- Plotting Omega scan products for {}'.format(channel.name))
    plot.write_qscan_plots(gps, channel, series, fscale=fscale,
                           colormap=colormap)
    # handle cross-correlation
    if correlate is not None:
        LOGGER.info(' -- Cross-correlating {}'.format(channel.name))
        correlation = omega.cross_correlate(series[2], correlate)
        channel.save_loudest_tile_features(
            series[3], correlation, gps=gps, dt=block.dt)
    else:
        channel.save_loudest_tile_features(series[3])
    # update the record of analyzed channels
    return html.update_toc(analyzed, channel, block_name)


# -- parse command-line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize argument parser
    parser = cli.create_parser(
        prog=PROG,
        description=__doc__,
    )

    # required argument
    parser.add_argument(
        'gpstime',
        type=to_gps,
        help='GPS time or datestring to scan',
    )

    # optional arguments
    cli.add_ifo_option(
        parser,
        required=False,
    )
    parser.add_argument(
        '-o',
        '--output-directory',
        help='output directory for the Omega scan, '
             'default: ~/public_html/wdq/{IFO}_{gpstime}',
    )
    parser.add_argument(
        '-f',
        '--config-file',
        action='append',
        default=None,
        help='path to configuration file to use, can be given '
             'multiple times (files read in order), default: '
             'choose a standard one based on IFO and GPS time',
    )
    parser.add_argument(
        '-d',
        '--disable-correlation',
        action='store_true',
        default=False,
        help='disable cross-correlation of aux '
             'channels, default: False',
    )
    parser.add_argument(
        '-D',
        '--disable-checkpoint',
        action='store_true',
        default=False,
        help='disable checkpointing from previous '
             'runs, default: False',
    )
    parser.add_argument(
        '-s',
        '--ignore-state-flags',
        action='store_true',
        default=False,
        help='ignore state flag definitions in '
             'the configuration, default: False',
    )
    parser.add_argument(
        '-t',
        '--far-threshold',
        type=float,
        default=3.171e-8,
        help='white noise false alarm rate threshold (Hz) for '
             'processing channels, default: %(default)s',
    )
    parser.add_argument(
        '-y',
        '--frequency-scaling',
        default='log',
        help='scaling of all frequency axes, default: %(default)s',
    )
    parser.add_argument(
        '-c',
        '--colormap',
        default='viridis',
        help='name of colormap to use, default: %(default)s',
    )
    cli.add_nproc_option(
        parser,
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the Omega scan command-line tool
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # enforce logging level
    LOGGER.setLevel('DEBUG')

    # get critical arguments
    ifo = args.ifo or 'Network'
    gps = numpy.around(float(args.gpstime), 2)
    LOGGER.info("{0} Omega Scan {1}".format(ifo, gps))

    # parse configuration files
    args.config_file = _parse_configuration(
        args.config_file, ifo=ifo, gps=gps)
    cp = config.OmegaConfigParser(ifo=ifo)
    cp.read(args.config_file)

    # parse primary channel
    if not args.disable_correlation:
        try:
            primary = config.OmegaChannelList(
                'primary', **dict(cp.items('primary')))
        except config.configparser.NoSectionError:
            LOGGER.warning('No primary configured, continuing '
                           'without cross-correlation')
            args.disable_correlation = True
    cp.remove_section('primary')

    # get contextual channel blocks
    blocks = cp.get_channel_blocks()

    # set up analyzed channel dict
    analyzed = _init_analyzed_channels()

    # prepare html variables
    htmlv = {
        'title': '{} Qscan | {}'.format(ifo, gps),
        'config': args.config_file,
        'prog': PROG,
        'refresh': True,
    }

    # set output directory
    indir = os.getcwd()
    outdir = os.path.abspath(
        args.output_directory or
        os.path.expanduser(
            '~/public_html/wdq/{ifo}_{gps}'.format(ifo=ifo, gps=gps),
        ))
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    os.chdir(outdir)
    LOGGER.debug('Output directory created as {}'.format(outdir))

    # make subdirectories
    for d in ['plots', 'about', 'data']:
        if not os.path.isdir(d):
            os.makedirs(d)

    # load checkpoints, if requested
    summary = os.path.join('data', 'summary.csv')
    (record, completed) = _load_channel_record(
        summary,
        use_checkpoint=(not args.disable_checkpoint),
        correlate=(not args.disable_correlation),
    )

    # set up html output
    LOGGER.debug('Setting up HTML at {}'.format(
        os.path.join(outdir, 'index.html')))
    html.write_qscan_page(ifo, gps, analyzed, **htmlv)

    # -- compute Q-scan ---------------

    # launch Omega scans
    LOGGER.info('Launching Omega scans')

    # construct a matched-filter from primary channel
    if not args.disable_correlation:
        LOGGER.debug('Processing primary channel')
        duration = primary.duration
        fftlength = primary.fftlength
        # process `duration` seconds of data centered on gps
        name = primary.channel.name
        start = gps - duration/2. - 1
        end = gps + duration/2. + 1
        correlate = get_data(
            name, start, end, frametype=primary.frametype,
            source=primary.source, nproc=args.nproc,
            verbose='Reading primary:'.rjust(30))
        correlate = omega.primary(
            gps, primary.length, correlate, fftlength,
            resample=primary.resample, f_low=primary.flow)
        plot.timeseries_plot(correlate, gps, primary.length, name,
                             'plots/primary.png', ylabel='Whitened Amplitude')
        # prepare HTML output
        htmlv['correlated'] = True
        htmlv['primary'] = name
    else:
        correlate = None

    # range over channel blocks
    for block in blocks.values():
        LOGGER.debug('Processing block {}'.format(block.key))
        chans = [c.name for c in block.channels]
        # get configuration
        duration = block.duration
        fftlength = block.fftlength
        # check that analysis flag is active for all of `duration`
        if block.flag and (not args.ignore_state_flags):
            LOGGER.info(' -- Querying state flag {}'.format(block.flag))
            if not check_flag(block.flag, gps, duration, pad=1):
                LOGGER.info(
                    ' -- {} not active, skipping block'.format(block.flag))
                continue
        # read `duration` seconds of data
        if not (set(chans) <= set(completed)):
            start = gps - duration/2. - 1
            end = gps + duration/2. + 1
            data = get_data(
                chans, start, end, frametype=block.frametype,
                source=block.source, nproc=args.nproc,
                verbose='Reading block:'.rjust(30))

        # process individual channels
        for channel in block.channels:
            if channel.name in completed:  # load checkpoint
                analyzed = _load_channel_from_checkpoint(
                    blocks[channel.section].name, channel, analyzed,
                    completed, record, (correlate is not None))
                htmlv['toc'] = analyzed
                html.write_qscan_page(ifo, gps, analyzed, **htmlv)
                continue

            analyzed = _scan_channel(
                channel, data[channel.name], analyzed, gps, block,
                args.far_threshold, (args.frequency_scaling == 'log'),
                args.frequency_scaling, args.colormap,
                blocks[channel.section].name, correlate)
            htmlv['toc'] = analyzed
            html.write_qscan_page(ifo, gps, analyzed, **htmlv)

    # -- finalize HTML ----------------

    # write HTML page and finish
    LOGGER.debug('Finalizing HTML at {}'.format(
        os.path.join(outdir, 'index.html')))
    _finalize_html(analyzed, ifo, gps, htmlv)
    LOGGER.info("-- index.html written, all done --")

    # return to original directory
    os.chdir(indir)


# -- run code -----------------------------------------------------------------

if __name__ == "__main__":
    main()
