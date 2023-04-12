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

import multiprocessing
import os
import re
import sys

from gwpy.timeseries import TimeSeries

import numpy

from MarkupPy import markup

from astropy.table import Table

from sklearn import linear_model
from sklearn.preprocessing import scale

from pandas import set_option

from gwpy.detector import ChannelList
from gwpy.io import nds2 as io_nds2

from .. import (cli, lasso as gwlasso)
from ..io.datafind import get_data
from ..io import html as htmlio

from matplotlib import (use, rcParams)
use('Agg')

# backend-dependent imports
from matplotlib.cm import get_cmap  # noqa: E402
from gwpy.plot import Plot  # noqa: E402
from gwdetchar.lasso import plot as gwplot  # noqa: E402
from gwdetchar.plot import texify  # noqa: E402

# LaTeX use
USETEX = rcParams["text.usetex"]

# default frametypes
DEFAULT_FRAMETYPE = {
    'GDS-CALIB_STRAIN': '{ifo}_HOFT_C00',
    'DMT-SNSH_EFFECTIVE_RANGE_MPC.mean': 'SenseMonitor_hoft_{ifo}_M',
    'DMT-SNSW_EFFECTIVE_RANGE_MPC.mean': 'SenseMonitor_CAL_{ifo}_M',
}

# set up logger
PROG = ('python -m gwdetchar.lasso' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())


# -- utilities ----------------------------------------------------------------

def _descaler(iterable, *coef):
    """Linear de-scaling of a data array
    """
    return (
        [((x * primary_std * coef[0]) + primary_mean) for x in iterable]
        if coef else [((x * primary_std) + primary_mean) for x in iterable]
    )


def _generate_cluster(input_):
    """Generate cluster data for use below
    """
    if USETEX:
        gwplot.configure_mpl_tex()
    currentchan = input_[1][0]
    currentts = input_[1][5]
    current = input_[0]
    p7 = (.135, .15, .95, .9)
    plot7 = None
    plot7_list = None

    if current < len(nonzerodata):
        cluster = []
        for i, otheritem in enumerate(list(auxdata.items())):
            chan_, ts_ = otheritem
            if chan_ != currentchan:
                pcorr = numpy.corrcoef(currentts.value, ts_.value)[0, 1]
                if abs(pcorr) >= cluster_threshold:
                    stub = re_delim.sub('_', chan_).replace('_', '-', 1)
                    cluster.append([i, ts_, pcorr, chan_, stub])

        if cluster:
            # write cluster table to file
            cluster = sorted(cluster, key=lambda x: abs(x[2]),
                             reverse=True)
            clustertab = Table(data=list(zip(*cluster))[2:4],
                               names=('Pearson Coefficient', 'Channel'))
            plot7_list = '%s_CLUSTER_LIST-%s.csv' % (
                re_delim.sub('_', str(currentchan)).replace('_', '-', 1),
                gpsstub)
            clustertab.write(plot7_list, format='csv', overwrite=True)

            ncluster = min(len(cluster), max_correlated_channels)
            colors2 = [cmap(i) for i in numpy.linspace(0, 1, ncluster+1)]

            # plot
            fig = Plot(figsize=(12, 4))
            fig.subplots_adjust(*p7)
            ax = fig.gca(xscale='auto-gps')
            ax.plot(
                times, scale(currentts.value)*numpy.sign(input_[1][1]),
                label=texify(currentchan), linewidth=line_size_aux,
                color=colors[0])

            for i in range(0, ncluster):
                this = cluster[i]
                ax.plot(
                    times,
                    scale(this[1].value) * numpy.sign(input_[1][1]) *
                    numpy.sign(this[2]),
                    color=colors2[i+1],
                    linewidth=line_size_aux,
                    label=('{0}, r = {1:.2}'.format(
                        texify(cluster[i][3]), cluster[i][2])),
                )

            ax.margins(x=0)
            ax.set_ylabel('Scaled amplitude [arbitrary units]')
            ax.set_title('Highly Correlated Channels')
            ax.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
            plot7 = gwplot.save_figure(fig, '%s_CLUSTER-%s.png' % (
                re_delim.sub('_', str(currentchan))
                        .replace('_', '-', 1),
                gpsstub), bbox_inches='tight')

    with counter.get_lock():
        counter.value += 1
        pc = 100 * counter.value / len(nonzerodata)
        LOGGER.info("Completed [%d/%d] %3d%% %-50s"
                    % (counter.value, len(nonzerodata), pc,
                       '(%s)' % str(currentchan)))
        sys.stdout.flush()
    return (plot7, plot7_list)


def _process_channel(input_):
    """Handle individual channels for multiprocessing
    """
    if USETEX:
        gwplot.configure_mpl_tex()
    p4 = (.1, .1, .9, .95)
    chan = input_[1][0]
    ts = input_[1][1]
    lassocoef = nonzerocoef[chan]
    zeroed = lassocoef == 0

    if zeroed:
        plot4 = None
        plot5 = None
        plot6 = None
        pcorr = None
    else:
        plot4 = None
        plot5 = None
        plot6 = None
        if trend_type == 'minute':
            pcorr = numpy.corrcoef(ts.value, primaryts.value)[0, 1]
        else:
            pcorr = 0.0
        if abs(lassocoef) < threshold:
            with counter.get_lock():
                counter.value += 1
            pc = 100 * counter.value / len(nonzerodata)
            LOGGER.info("Completed [%d/%d] %3d%% %-50s"
                        % (counter.value, len(nonzerodata), pc,
                           '(%s)' % str(chan)))
            sys.stdout.flush()
            return (chan, lassocoef, plot4, plot5, plot6, ts)

        # create time series subplots
        fig = Plot(figsize=(12, 8))
        fig.subplots_adjust(*p4)
        ax1 = fig.add_subplot(2, 1, 1, xscale='auto-gps', epoch=start)
        ax1.plot(primaryts, label=texify(primary), color='black',
                 linewidth=line_size_primary)
        ax1.set_xlabel(None)
        ax2 = fig.add_subplot(2, 1, 2, sharex=ax1, xlim=xlim)
        ax2.plot(ts, label=texify(chan), linewidth=line_size_aux)
        if range_is_primary:
            ax1.set_ylabel('Sensitive range [Mpc]')
        else:
            ax1.set_ylabel('Primary channel units')
        ax2.set_ylabel('Channel units')
        for ax in fig.axes:
            ax.legend(loc='best')
        channelstub = re_delim.sub('_', str(chan)).replace('_', '-', 1)
        plot4 = gwplot.save_figure(
            fig, '%s_TRENDS-%s.png' % (channelstub, gpsstub),
            bbox_inches='tight')

        # create scaled, sign-corrected, and overlayed timeseries
        tsscaled = scale(ts.value)
        if lassocoef < 0:
            tsscaled = numpy.negative(tsscaled)
        fig = Plot(figsize=(12, 4))
        fig.subplots_adjust(*p1)
        ax = fig.gca(xscale='auto-gps', epoch=start, xlim=xlim)
        ax.plot(times, _descaler(target), label=texify(primary),
                color='black', linewidth=line_size_primary)
        ax.plot(times, _descaler(tsscaled), label=texify(chan),
                linewidth=line_size_aux)
        if range_is_primary:
            ax.set_ylabel('Sensitive range [Mpc]')
        else:
            ax.set_ylabel('Primary Channel Units')
        ax.legend(loc='best')
        plot5 = gwplot.save_figure(
            fig, '%s_COMPARISON-%s.png' % (channelstub, gpsstub),
            bbox_inches='tight')

        # scatter plot
        tsCopy = ts.value.reshape(-1, 1)
        primarytsCopy = primaryts.value.reshape(-1, 1)
        primaryReg = linear_model.LinearRegression()
        primaryReg.fit(tsCopy, primarytsCopy)
        primaryFit = primaryReg.predict(tsCopy)
        fig = Plot(figsize=(12, 4))
        fig.subplots_adjust(*p1)
        ax = fig.gca()
        ax.set_xlabel(texify(chan) + ' [Channel units]')
        if range_is_primary:
            ax.set_ylabel('Sensitive range [Mpc]')
        else:
            ax.set_ylabel('Primary channel units')
        y_min = min(primaryts.value)
        y_max = max(primaryts.value)
        y_range = y_max - y_min
        ax.set_ylim(y_min - (y_range * 0.1), y_max + (y_range * 0.1))
        ax.text(.9, .1, 'r = ' + str('{0:.2}'.format(pcorr)),
                verticalalignment='bottom', horizontalalignment='right',
                transform=ax.transAxes, color='black', size=20,
                bbox=dict(boxstyle='square', facecolor='white', alpha=.75,
                          edgecolor='black'))
        ax.scatter(ts.value, primaryts.value, color='red')
        ax.plot(ts.value, primaryFit, color='black')
        ax.autoscale_view(tight=False, scalex=True, scaley=True)
        plot6 = gwplot.save_figure(
            fig, '%s_SCATTER-%s.png' % (channelstub, gpsstub),
            bbox_inches='tight')

    # increment counter and print status
    with counter.get_lock():
        counter.value += 1
        pc = 100 * counter.value / len(nonzerodata)
        LOGGER.info("Completed [%d/%d] %3d%% %-50s"
                    % (counter.value, len(nonzerodata), pc,
                       '(%s)' % str(chan)))
        sys.stdout.flush()
    return (chan, lassocoef, plot4, plot5, plot6, ts)


def get_primary_ts(channel, start, end, filepath=None,
                   frametype=None, cache=None, nproc=1):
    """Retrieve primary channel timeseries
    by either reading a .gwf file or querying
    """
    if filepath is not None:
        LOGGER.info('Reading primary channel file')
        return TimeSeries.read(filepath, channel=channel, start=start, end=end,
                               format='gwf', nproc=nproc)
    else:
        LOGGER.info('Querying primary channel')
        return get_data(channel, start, end,
                        verbose='Reading primary:'.rjust(30),
                        frametype=frametype, source=cache, nproc=nproc)


# -- parse command line -------------------------------------------------------

def create_parser():
    """Create a command-line parser for this entry point
    """
    # initialize argument parser
    parser = cli.create_parser(
        prog=PROG,
        description=__doc__,
        formatter_class=cli.argparse.ArgumentDefaultsHelpFormatter,
    )
    psig = parser.add_argument_group('Signal processing options')
    lsig = parser.add_argument_group('Lasso options')

    # required arguments
    cli.add_gps_start_stop_arguments(parser)
    cli.add_ifo_option(parser)

    # optional arguments
    cli.add_nproc_option(parser, default=1)
    parser.add_argument(
        '-J',
        '--nproc-plot',
        type=int,
        default=None,
        help='number of processes to use for plot rendering, '
             'will be ignored if not using LaTeX',
    )
    parser.add_argument(
        '-o',
        '--output-dir',
        default=os.curdir,
        type=os.path.abspath,
        help='output directory for plots',
    )
    parser.add_argument(
        '-f',
        '--channel-file',
        type=os.path.abspath,
        help='path for channel file',
    )
    parser.add_argument(
        '-T',
        '--trend-type',
        default='minute',
        choices=['second', 'minute'],
        help='type of trend for correlation',
    )
    parser.add_argument(
        '-p',
        '--primary-channel',
        default='{ifo}:DMT-SNSH_EFFECTIVE_RANGE_MPC.mean',
        help='name of primary channel to use',
    )
    # primary channel filepath argument
    parser.add_argument(
        '-pf',
        '--primary-file',
        default=None,
        help='filepath of .gwf custom primary channel if using custom channel'
    )
    parser.add_argument(
        '-P',
        '--primary-frametype',
        default=None,
        help='frametype for --primary-channel, default: guess by channel name',
    )
    parser.add_argument(
        '--primary-cache',
        default=None,
        help='cache file for --primary-channel, default: None',
    )
    parser.add_argument(
        '-O',
        '--remove-outliers',
        type=float,
        default=None,
        help='Std. dev. limit for removing outliers',
    )
    parser.add_argument(
        '-R',
        '--remove-outliers-pf',
        type=float,
        default=None,
        help='Fractional limit for removing outliers between 0 and 1',
    )
    parser.add_argument(
        '-t',
        '--threshold',
        type=float,
        default=0.0001,
        help='threshold for making a plot',
    )

    # signal processing arguments
    psig.add_argument(
        '-b',
        '--band-pass',
        type=float,
        nargs=2,
        default=None,
        metavar="FLOW FHIGH",
        help='lower and upper frequencies for bandpass on h(t)',
    )
    psig.add_argument(
        '-x',
        '--filter-padding',
        type=float,
        default=3.,
        help='amount of time (seconds) to pad data for filtering',
    )

    # lasso arguments
    lsig.add_argument(
        '-a',
        '--alpha',
        default=None,
        type=float,
        help='alpha parameter for lasso fit',
    )
    lsig.add_argument(
        '-C',
        '--no-cluster',
        action='store_true',
        default=False,
        help='do not generate clustered channel plots',
    )
    lsig.add_argument(
        '-c',
        '--cluster-coefficient',
        default=.85,
        type=float,
        help='correlation coefficient threshold for clustering',
    )
    lsig.add_argument(
        '-L',
        '--line-size-primary',
        default=1,
        type=float,
        help='line width of primary channel',
    )
    lsig.add_argument(
        '-l',
        '--line-size-aux',
        default=0.75,
        type=float,
        help='line width of auxilary channel',
    )

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the lasso command-line interface
    """
    # declare global variables
    # this is needed for multiprocessing utilities
    global auxdata, cluster_threshold, cmap, colors, counter, gpsstub
    global line_size_aux, line_size_primary, max_correlated_channels
    global nonzerocoef, nonzerodata, p1, primary, primary_mean, primary_std
    global primaryts, range_is_primary, re_delim, start, target, times
    global threshold, trend_type, xlim
    parser = create_parser()
    args = parser.parse_args(args=args)

    # check for correct input
    if args.remove_outliers_pf:
        if args.remove_outliers_pf >= 1 or args.remove_outliers_pf <= 0:
            raise ValueError('Percent outlier limit must be between 0 and 1')

    # get run params
    start = int(args.gpsstart)
    end = int(args.gpsend)
    pad = args.filter_padding

    # set pertinent global variables
    cluster_threshold = args.cluster_coefficient
    line_size_aux = args.line_size_aux
    line_size_primary = args.line_size_primary
    threshold = args.threshold
    trend_type = args.trend_type

    # let's go
    LOGGER.info('{} Lasso correlations {}-{}'.format(args.ifo, start, end))

    # get primary channel frametype
    primary = args.primary_channel.format(ifo=args.ifo)
    range_is_primary = 'EFFECTIVE_RANGE_MPC' in args.primary_channel
    if args.primary_cache is not None:
        LOGGER.info("Using custom primary cache file")
    elif args.primary_frametype is None and args.primary_file is None:
        try:
            args.primary_frametype = DEFAULT_FRAMETYPE[
                primary.split(':')[1]].format(ifo=args.ifo)
        except KeyError as exc:
            raise type(exc)("Could not determine primary channel's frametype, "
                            "please specify with --primary-frametype")

    # create output directory
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

    # multiprocessing for plots
    nprocplot = (args.nproc_plot or args.nproc) if USETEX else 1

    # bandpass primary
    if args.band_pass:
        try:
            flower, fupper = args.band_pass
        except TypeError:
            flower, fupper = None

        LOGGER.info("-- Loading primary channel data")
        bandts = get_primary_ts(filepath=args.primary_file, channel=primary,
                                start=start-pad, end=end+pad,
                                frametype=args.primary_frametype,
                                cache=args.primary_cache, nproc=args.nproc)
        if flower < 0 or fupper >= float((bandts.sample_rate/2.).value):
            raise ValueError(
                "bandpass frequency is out of range for this "
                "channel, band (Hz): {0}, sample rate: {1}".format(
                    args.band_pass, bandts.sample_rate))

        # get darm BLRMS
        LOGGER.debug("-- Filtering data")
        if trend_type == 'minute':
            stride = 60
        else:
            stride = 1
        if flower:
            darmbl = (
                bandts.highpass(flower/2., fstop=flower/4.,
                                filtfilt=False, ftype='butter')
                .notch(60, filtfilt=False)
                .bandpass(flower, fupper, fstop=[flower/2., fupper*1.5],
                          filtfilt=False, ftype='butter')
                .crop(start, end))
            darmblrms = darmbl.rms(stride)
            darmblrms.name = '%s %s-%s Hz BLRMS' % (primary, flower, fupper)
        else:
            darmbl = bandts.notch(60).crop(start, end)
            darmblrms = darmbl.rms(stride)
            darmblrms.name = '%s RMS' % primary

        primaryts = darmblrms

        bandts_asd = bandts.asd(4, 2, method='median')
        darmbl_asd = darmbl.asd(4, 2, method='median')

        spectrum_plots = gwplot.make_spectrum_plots(
            start, end, flower, fupper, primary,
            bandts_asd, darmbl_asd)
        spectrum_plot_zoomed_out = spectrum_plots[0]
        spectrum_plot_zoomed_in = spectrum_plots[1]

    else:
        # load primary channel data
        LOGGER.info("-- Loading primary channel data")
        primaryts = get_primary_ts(filepath=args.primary_file, channel=primary,
                                   start=start, end=end,
                                   frametype=args.primary_frametype,
                                   cache=args.primary_cache,
                                   nproc=args.nproc).crop(start, end)

    if args.remove_outliers:
        LOGGER.debug(
            "-- Removing outliers above %f sigma" % args.remove_outliers)
        gwlasso.remove_outliers(primaryts, args.remove_outliers)
    elif args.remove_outliers_pf:
        LOGGER.debug("-- Removing outliers in the bottom {} percent "
                     "of data".format(args.remove_outliers_pf*100))
        gwlasso.remove_outliers(
            primaryts, args.remove_outliers_pf, method='pf')
        start = int(primaryts.span[0])
        end = int(primaryts.span[1])

    primary_mean = numpy.mean(primaryts.value)
    primary_std = numpy.std(primaryts.value)

    # get aux data
    LOGGER.info("-- Loading auxiliary channel data")
    if args.channel_file is None:
        host, port = io_nds2.host_resolution_order(args.ifo)[0]
        channels = ChannelList.query_nds2('*.mean', host=host, port=port,
                                          type='m-trend')
    else:
        with open(args.channel_file, 'r') as f:
            channels = [name.rstrip('\n') for name in f]
    nchan = len(channels)
    LOGGER.debug("Identified %d channels" % nchan)

    if trend_type == 'minute':
        frametype = '%s_M' % args.ifo  # for minute trends
    else:
        frametype = '%s_T' % args.ifo  # for second trends

    # read aux channels
    auxdata = get_data(
        channels, start, end, verbose='Reading:'.rjust(30),
        frametype=frametype, nproc=args.nproc, pad=0).crop(start, end)

    # -- removes flat data to be re-introdused later

    LOGGER.info('-- Pre-processing auxiliary channel data')

    auxdata = gwlasso.remove_flat(auxdata)
    flatable = Table(data=(list(set(channels) - set(auxdata.keys())),),
                     names=('Channels',))
    LOGGER.debug('Removed {0} channels with flat data'.format(len(flatable)))
    LOGGER.debug('{0} channels remaining'.format(len(auxdata)))

    # -- remove bad data

    LOGGER.info("Removing any channels with bad data...")
    nbefore = len(auxdata)
    auxdata = gwlasso.remove_bad(auxdata)
    nafter = len(auxdata)
    LOGGER.debug('Removed {0} channels with bad data'.format(nbefore - nafter))
    LOGGER.debug('{0} channels remaining'.format(nafter))
    data = numpy.array([scale(ts.value) for ts in auxdata.values()]).T

    # -- perform lasso regression -------------------

    # create model
    LOGGER.info('-- Fitting data to target')
    target = scale(primaryts.value)
    model = gwlasso.fit(data, target, alpha=args.alpha)
    LOGGER.info('Alpha: {}'.format(model.alpha))

    # restructure results for convenience
    allresults = Table(
        data=(list(auxdata.keys()), model.coef_, numpy.abs(model.coef_)),
        names=('Channel', 'Lasso coefficient', 'rank'))
    allresults.sort('rank')
    allresults.reverse()
    useful = allresults['rank'] > 0
    allresults.remove_column('rank')
    results = allresults[useful]  # non-zero coefficient
    zeroed = allresults[numpy.invert(useful)]  # zero coefficient

    # extract data for useful channels
    nonzerodata = {name: auxdata[name] for name in results['Channel']}
    nonzerocoef = {name: coeff for name, coeff in results.as_array()}

    # print results
    LOGGER.info('Found {} channels with |Lasso coefficient| >= {}:\n\n'.format(
                len(results), threshold))
    print(results)
    print('\n\n')

    # convert to pandas
    set_option('max_colwidth', -1)
    df = results.to_pandas()
    df.index += 1

    # write results to files
    gpsstub = '%d-%d' % (start, end-start)
    resultsfile = '%s-LASSO_RESULTS-%s.csv' % (args.ifo, gpsstub)
    results.write(resultsfile, format='csv', overwrite=True)
    zerofile = '%s-ZERO_COEFFICIENT_CHANNELS-%s.csv' % (args.ifo, gpsstub)
    zeroed.write(zerofile, format='csv', overwrite=True)
    flatfile = '%s-FLAT_CHANNELS-%s.csv' % (args.ifo, gpsstub)
    flatable.write(flatfile, format='csv', overwrite=True)

    # -- generate lasso plots

    modelFit = model.predict(data)

    re_delim = re.compile(r'[:_-]')
    p1 = (.1, .15, .9, .9)  # global plot defaults for plot1, lasso model

    times = primaryts.times.value
    xlim = primaryts.span
    cmap = get_cmap('tab20')
    colors = [cmap(i) for i in numpy.linspace(0, 1, len(nonzerodata)+1)]

    plot = Plot(figsize=(12, 4))
    plot.subplots_adjust(*p1)
    ax = plot.gca(xscale='auto-gps', epoch=start, xlim=xlim)
    ax.plot(times, _descaler(target), label=texify(primary),
            color='black', linewidth=line_size_primary)
    ax.plot(times, _descaler(modelFit), label='Lasso model',
            linewidth=line_size_aux)
    if range_is_primary:
        ax.set_ylabel('Sensitive range [Mpc]')
        ax.set_title('Lasso Model of Range')
    else:
        ax.set_ylabel('Primary Channel Units')
        ax.set_title('Lasso Model of Primary Channel')
    ax.legend(loc='best')
    plot1 = gwplot.save_figure(
         plot, '%s-LASSO_MODEL-%s.png' % (args.ifo, gpsstub),
         bbox_inches='tight')

    # summed contributions
    plot = Plot(figsize=(12, 4))
    plot.subplots_adjust(*p1)
    ax = plot.gca(xscale='auto-gps', epoch=start, xlim=xlim)
    ax.plot(times, _descaler(target), label=texify(primary),
            color='black', linewidth=line_size_primary)
    summed = 0
    for i, name in enumerate(results['Channel']):
        summed += scale(nonzerodata[name].value) * nonzerocoef[name]
        if i:
            label = 'Channels 1-{0}'.format(i+1)
        else:
            label = 'Channel 1'
        ax.plot(times, _descaler(summed), label=label, color=colors[i],
                linewidth=line_size_aux)
    if range_is_primary:
        ax.set_ylabel('Sensitive range [Mpc]')
    else:
        ax.set_ylabel('Primary Channel Units')
    ax.set_title('Summations of Channel Contributions to Model')
    ax.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
    plot2 = gwplot.save_figure(
        plot, '%s-LASSO_CHANNEL_SUMMATION-%s.png' % (args.ifo, gpsstub),
        bbox_inches='tight')

    # individual contributions
    plot = Plot(figsize=(12, 4))
    plot.subplots_adjust(*p1)
    ax = plot.gca(xscale='auto-gps', epoch=start, xlim=xlim)
    ax.plot(times, _descaler(target), label=texify(primary),
            color='black', linewidth=line_size_primary)
    for i, name in enumerate(results['Channel']):
        this = _descaler(scale(nonzerodata[name].value) * nonzerocoef[name])
        if i:
            label = 'Channels 1-{0}'.format(i+1)
        else:
            label = 'Channel 1'
        ax.plot(times, this, label=texify(name), color=colors[i],
                linewidth=line_size_aux)
    if range_is_primary:
        ax.set_ylabel('Sensitive range [Mpc]')
    else:
        ax.set_ylabel('Primary Channel Units')
    ax.set_title('Individual Channel Contributions to Model')
    ax.legend(loc='center left', bbox_to_anchor=(1.05, 0.5))
    plot3 = gwplot.save_figure(
        plot, '%s-LASSO_CHANNEL_CONTRIBUTIONS-%s.png' % (args.ifo, gpsstub),
        bbox_inches='tight')

    # -- process aux channels, making plots

    LOGGER.info("-- Processing channels")
    counter = multiprocessing.Value('i', 0)

    # process channels
    pool = multiprocessing.Pool(nprocplot)
    results = pool.map(_process_channel, enumerate(list(nonzerodata.items())))
    results = sorted(results, key=lambda x: abs(x[1]), reverse=True)

    #  generate clustered time series plots
    counter = multiprocessing.Value('i', 0)
    max_correlated_channels = 20

    if args.no_cluster is False:
        LOGGER.info("-- Generating clusters")
        pool = multiprocessing.Pool(nprocplot)
        clusters = pool.map(_generate_cluster, enumerate(results))

    channelsfile = '%s-CHANNELS-%s.csv' % (args.ifo, gpsstub)
    numpy.savetxt(channelsfile, channels, delimiter=',', fmt='%s')

    # write html
    trange = '%d-%d' % (start, end)
    title = '%s Lasso Correlation: %s' % (args.ifo, trange)
    if args.band_pass:
        links = [trange] + [(s, '#%s' % s.lower()) for s in
                            ['Parameters', 'Spectra', 'Model', 'Results']]
    else:
        links = [trange] + [(s, '#%s' % s.lower()) for s in
                            ['Parameters', 'Model', 'Results']]
    (brand, class_) = htmlio.get_brand(args.ifo, 'Lasso', start)
    navbar = htmlio.navbar(links, class_=class_, brand=brand)
    page = htmlio.new_bootstrap_page(
        title='%s Lasso | %s' % (args.ifo, trange),
        navbar=navbar)
    page.h1(title, class_='pb-2 mt-3 mb-2 border-bottom')

    # -- summary table
    content = [
        ('Primary channel', markup.oneliner.code(primary)),
        ('Primary frametype', markup.oneliner.code(
            args.primary_frametype) or '-'),
        ('Primary cache file', markup.oneliner.code(
            args.primary_cache) or '-'),
        ('Outlier threshold', '%s sigma' % args.remove_outliers),
        ('Lasso coefficient threshold', str(threshold)),
        ('Cluster coefficient threshold', str(args.cluster_coefficient)),
        ('Non-zero coefficients', str(numpy.count_nonzero(model.coef_))),
        ('&alpha; (model)', '%.4f' % model.alpha)]
    if args.band_pass:
        content.insert(2, ('Primary bandpass',
                           '{0}-{1} Hz'.format(flower, fupper)))
    page.h2('Parameters', class_='mt-4 mb-4', id_='parameters')
    page.div(class_='row')
    page.div(class_='col-md-9 col-sm-12')
    page.add(htmlio.parameter_table(content, start=start, end=end))
    page.div.close()  # col-md-9 col-sm-12

    # -- download button
    files = [
        ('%s analyzed channels (CSV)' % nchan, channelsfile),
        ('%s flat channels (CSV)' % len(flatable), flatfile),
        ('%s zeroed channels (CSV)' % len(zeroed), zerofile)]
    page.div(class_='col-md-3 col-sm-12')
    page.add(htmlio.download_btn(
        files, label='Channel information',
        btnclass='btn btn-%s dropdown-toggle' % args.ifo.lower()))
    page.div.close()  # col-md-3 col-sm-12
    page.div.close()  # rowa

    # -- command-line
    page.h5('Command-line:')
    page.add(htmlio.get_command_line(about=False, prog=PROG))

    if args.band_pass:
        page.h2('Primary channel spectra', class_='mt-4', id_='spectra')
        page.div(class_='card border-light card-body shadow-sm')
        page.div(class_='row')
        page.div(class_='col-md-6')
        spectra_img1 = htmlio.FancyPlot(spectrum_plot_zoomed_out)
        page.add(htmlio.fancybox_img(spectra_img1))
        page.div.close()  # col-md-6
        page.div(class_='col-md-6')
        spectra_img2 = htmlio.FancyPlot(spectrum_plot_zoomed_in)
        page.add(htmlio.fancybox_img(spectra_img2))
        page.div.close()  # col-md-6
        page.div.close()  # row
        page.div.close()  # card border-light card-body shadow-sm

    # -- model information
    page.h2('Model information', class_='mt-4', id_='model')

    page.div(class_='card card-%s card-body shadow-sm' % args.ifo.lower())
    page.div(class_='row')
    page.div(class_='col-md-8 offset-md-2', id_='results-table')
    page.p('Below are the top {} mean minute-trend channels, ranked by '
           'Lasso correlation with the primary.'.format(df.shape[0]))
    page.add(df.to_html(
        classes=('table', 'table-sm', 'table-hover'),
        formatters={
            'Lasso coefficient': lambda x: "%.4f" % x,
            'Channel': lambda x: str(htmlio.cis_link(x.split('.')[0])),
            '__index__': lambda x: str(x)
        },
        escape=False,
        border=0).replace(' style="text-align: right;"', ''))
    page.div.close()  # col-md-10 offset-md-1
    page.div.close()  # row

    page.div(class_='row', id_='primary-lasso')
    page.div(class_='col-md-8 offset-md-2')
    img1 = htmlio.FancyPlot(plot1)
    page.add(htmlio.fancybox_img(img1))  # primary lasso plot
    page.div.close()  # col-md-8 offset-md-2
    page.div.close()  # primary-lasso

    page.div(class_='row', id_='channel-summation')
    img2 = htmlio.FancyPlot(plot2)
    page.div(class_='col-md-8 offset-md-2')
    page.add(htmlio.fancybox_img(img2))
    page.div.close()  # col-md-8 offset-md-2
    page.div.close()  # channel-summation

    page.div(class_='row', id_='channels-and-primary')
    img3 = htmlio.FancyPlot(plot3)
    page.div(class_='col-md-8 offset-md-2')
    page.add(htmlio.fancybox_img(img3))
    page.div.close()  # col-md-8 offset-md-2
    page.div.close()  # channels-and-primary

    page.div.close()  # card card-<ifo> card-body shadow-sm

    # -- results
    page.h2('Top channels', class_='mt-4', id_='results')
    page.div(id_='results')
    # for each aux channel, create information container and put plots in it
    for i, (ch, lassocoef, plot4, plot5, plot6, ts) in enumerate(results):
        # set container color/context based on lasso coefficient
        if lassocoef == 0:
            break
        elif abs(lassocoef) < threshold:
            h = '%s [lasso coefficient = %.4f] (Below threshold)' % (
                ch, lassocoef)
        else:
            h = '%s [lasso coefficient = %.4f]' % (ch, lassocoef)
        if ((lassocoef is None) or (lassocoef == 0)
                or (abs(lassocoef) < threshold)):
            card = 'card border-light mb-1 shadow-sm'
            card_header = 'card-header bg-light'
        elif abs(lassocoef) >= .5:
            card = 'card border-danger mb-1 shadow-sm'
            card_header = 'card-header text-white bg-danger'
        elif abs(lassocoef) >= .2:
            card = 'card border-warning mb-1 shadow-sm'
            card_header = 'card-header text-white bg-warning'
        else:
            card = 'card border-info mb-1 shadow-sm'
            card_header = 'card-header text-white bg-info'
        page.div(class_=card)

        # heading
        page.div(class_=card_header)
        page.a(h, class_='collapsed card-link cis-link', href='#channel%d' % i,
               **{'data-toggle': 'collapse'})
        page.div.close()  # card-header
        # body
        page.div(id_='channel%d' % i, class_='collapse',
                 **{'data-parent': '#results'})
        page.div(class_='card-body')
        if lassocoef is None:
            page.p('The amplitude data for this channel is flat (does not '
                   'change) within the chosen time period.')
        elif abs(lassocoef) < threshold:
            page.p('Lasso coefficient below the threshold of %g.'
                   % (threshold))
        else:
            for image in [plot4, plot5, plot6]:
                img = htmlio.FancyPlot(image)
                page.div(class_='row')
                page.div(class_='col-md-8 offset-md-2')
                page.add(htmlio.fancybox_img(img))
                page.div.close()  # col-md-8 offset-md-2
                page.div.close()  # row
                page.add('<hr class="row-divider">')
            if args.no_cluster is False:
                if clusters[i][0] is None:
                    page.p("<font size='3'><br />No channels were highly "
                           "correlated with this channel.</font>")
                else:
                    page.div(class_='row', id_='clusters')
                    page.div(class_='col-md-12')
                    cimg = htmlio.FancyPlot(clusters[i][0])
                    page.add(htmlio.fancybox_img(cimg))
                    page.div.close()  # col-md-12
                    page.div.close()  # clusters
                    if clusters[i][1] is not None:
                        corr_link = markup.oneliner.a(
                            'Export {} channels (CSV)'.format(
                                max_correlated_channels),
                            href=clusters[i][1], download=clusters[i][1],
                        )
                        page.button(
                            corr_link,
                            class_='btn btn-%s' % args.ifo.lower(),
                        )
        page.div.close()  # card-body
        page.div.close()  # collapse
        page.div.close()  # card
    page.div.close()  # results
    htmlio.close_page(page, 'index.html')  # save and close
    LOGGER.info("-- Process Completed")


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
