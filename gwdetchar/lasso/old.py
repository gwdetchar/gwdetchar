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
import numpy
import os
import re
import sys

from scipy.stats import spearmanr

from gwpy.detector import ChannelList
from gwpy.io import nds2 as io_nds2

from .. import (cli, lasso as gwlasso)
from ..io import html as htmlio
from ..io.datafind import get_data

from sklearn import linear_model

from matplotlib import use
use('Agg')

# backend-dependent import
import matplotlib.pyplot as plt  # noqa: E402
from gwpy.plot import Plot  # noqa: E402

# initialize logger
PROG = ('python -m gwdetchar.lasso.old' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())


# -- parse command-line -------------------------------------------------------

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
        help='number of processes to use for plotting',
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
        default='{ifo}:GDS-CALIB_STRAIN',
        help='name of primary channel to use',
    )
    parser.add_argument(
        '-P',
        '--primary-frametype',
        help='frametype for --primary-channel',
    )
    parser.add_argument(
        '-r',
        '--range-channel',
        default='{ifo}:DMT-SNSH_EFFECTIVE_RANGE_MPC.mean',
        help='name of range channel to use',
    )
    parser.add_argument(
        '-R',
        '--range-frametype',
        help='frametype for --range-channel',
    )
    parser.add_argument(
        '-O',
        '--remove-outliers',
        type=float,
        default=None,
        help='Std. dev. limit for removing outliers',
    )
    parser.add_argument(
        '-t',
        '--threshold',
        type=float,
        default=0.1,
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

    # return the argument parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the old lasso command-line interface
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    start = int(args.gpsstart)
    end = int(args.gpsend)
    pad = args.filter_padding
    try:
        flower, fupper = args.band_pass
    except TypeError:
        flower, fupper = None

    LOGGER.info('{} Slow Correlation {}-{}'.format(args.ifo, start, end))

    if args.primary_channel == '{ifo}:GDS-CALIB_STRAIN':
        args.primary_frametype = '%s_HOFT_C00' % args.ifo
    primary = args.primary_channel.format(ifo=args.ifo)
    rangechannel = args.range_channel.format(ifo=args.ifo)

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    os.chdir(args.output_dir)
    nprocplot = args.nproc_plot or args.nproc

    # load data
    LOGGER.info("-- Loading range data")
    rangets = get_data(
        rangechannel, start, end, frametype=args.range_frametype,
        verbose=True, nproc=args.nproc)

    if args.trend_type == 'minute':
        dstart, dend = rangets.span
    else:
        dstart = start
        dend = end

    LOGGER.info("-- Loading h(t) data")
    darmts = get_data(primary, dstart-pad, dend+pad, verbose=True,
                      frametype=args.primary_frametype, nproc=args.nproc)

    # get darm BLRMS
    LOGGER.debug("-- Filtering h(t) data")
    if args.trend_type == 'minute':
        stride = 60
    else:
        stride = 1
    if flower:
        darmblrms = (
            darmts.highpass(flower/2., fstop=flower/4.,
                            filtfilt=False, ftype='butter')
            .notch(60, filtfilt=False)
            .bandpass(flower, fupper, fstop=[flower/2., fupper*1.5],
                      filtfilt=False, ftype='butter')
            .crop(dstart, dend).rms(stride))
        darmblrms.name = '%s %s-%s Hz BLRMS' % (primary, flower, fupper)
    else:
        darmblrms = darmts.notch(60).crop(dstart, dend).rms(stride)
        darmblrms.name = '%s RMS' % primary

    if args.remove_outliers:
        LOGGER.debug(
            "-- Removing outliers above %f sigma" % args.remove_outliers)
        gwlasso.remove_outliers(darmblrms, args.remove_outliers)
        gwlasso.remove_outliers(rangets, args.remove_outliers)

    if args.trend_type == 'minute':
        # calculate the r value between the DARM BLRMS and the Range timeseries
        corr_p = numpy.corrcoef(rangets.value, darmblrms.value)[0, 1]
        # calculate the ρ value between the DARM BLRMS and the Range timeseries
        corr_s = spearmanr(rangets.value, darmblrms.value)[0]
    else:
        # for second trends, set correlation to 0 since sample rates differ
        corr_p = 0
        corr_s = 0

    # create scaled versions of data to compare to each other
    LOGGER.debug("-- Creating scaled data")
    rangescaled = rangets.detrend()
    rangerms = numpy.sqrt(sum(rangescaled**2.0)/len(rangescaled))
    darmscaled = darmblrms.detrend()
    darmrms = numpy.sqrt(sum(darmscaled**2.0)/len(darmscaled))

    # create scaled darm using the rms(range) and the rms(darm)
    if args.trend_type == 'minute':
        darmscaled *= (-rangerms / darmrms)

    # get aux data
    LOGGER.info("-- Loading auxiliary channel data")
    host, port = io_nds2.host_resolution_order(args.ifo)[0]
    if args.channel_file is None:
        channels = ChannelList.query_nds2('*.mean', host=host, port=port,
                                          type='m-trend')
    else:
        with open(args.channel_file, 'r') as f:
            channels = f.read().rstrip('\n').split('\n')
    nchan = len(channels)
    LOGGER.debug("Identified %d channels" % nchan)
    if args.trend_type == 'minute':
        frametype = '%s_M' % args.ifo  # for minute trends
    else:
        frametype = '%s_T' % args.ifo  # for second trends
    auxdata = get_data(
        list(map(str, channels)), dstart, dend, verbose=True,
        pad=0, frametype=frametype, nproc=args.nproc)

    gpsstub = '%d-%d' % (start, end-start)
    re_delim = re.compile('[:_-]')

    LOGGER.info("-- Processing channels")
    counter = multiprocessing.Value('i', 0)

    p1 = (.1, .1, .9, .95)
    p2 = (.1, .15, .9, .9)

    def process_channel(input_,):
        chan, ts = input_
        flat = ts.value.min() == ts.value.max()
        if flat:
            corr1 = None
            corr2 = None
            corr1s = None
            corr2s = None
            plot1 = None
            plot2 = None
            plot3 = None
        else:
            corr1 = numpy.corrcoef(ts.value, darmblrms.value)[0, 1]
            corr1s = spearmanr(ts.value, darmblrms.value)[0]
            if args.trend_type == 'minute':
                corr2 = numpy.corrcoef(ts.value, rangets.value)[0, 1]
                corr2s = spearmanr(ts.value, rangets.value)[0]
            else:
                corr2 = 0.0
                corr2s = 0.0
            # if all corralations are below threshold it does not plot
            if ((abs(corr1) < args.threshold)
               and (abs(corr1s) < args.threshold)
               and (abs(corr2) < args.threshold)
               and (abs(corr2s) < args.threshold)):
                plot1 = None
                plot2 = None
                plot3 = None
                return (chan, corr1, corr2, plot1,
                        plot2, plot3, corr1s, corr2s)

            plot = Plot(darmblrms, ts, rangets,
                        xscale="auto-gps", separate=True,
                        figsize=(12, 12))
            plot.subplots_adjust(*p1)
            plot.axes[0].set_ylabel('$h(t)$ BLRMS [strain]')
            plot.axes[1].set_ylabel('Channel units')
            plot.axes[2].set_ylabel('Sensitive range [Mpc]')
            for ax in plot.axes:
                ax.legend(loc='best')
                ax.set_xlim(start, end)
                ax.set_epoch(start)
            channelstub = re_delim.sub('_', str(chan)).replace('_', '-', 1)
            plot1 = '%s_TRENDS-%s.png' % (channelstub, gpsstub)
            try:
                plot.save(plot1)
            except (IOError, IndexError):
                plot.save(plot1)
            except RuntimeError as e:
                if 'latex' in str(e).lower():
                    plot.save(plot1)
                else:
                    raise
            plot.close()

            # plot auto-scaled verions
            tsscaled = ts.detrend()
            tsrms = numpy.sqrt(sum(tsscaled**2.0)/len(tsscaled))
            if args.trend_type == 'minute':
                tsscaled *= (rangerms / tsrms)
                if corr1 > 0:
                    tsscaled *= -1
            else:
                tsscaled *= (darmrms / tsrms)
                if corr1 < 0:
                    tsscaled *= -1
            plot = Plot(darmscaled, rangescaled, tsscaled,
                        xscale="auto-gps", figsize=[12, 6])
            plot.subplots_adjust(*p2)
            ax = plot.gca()
            ax.set_xlim(start, end)
            ax.set_epoch(start)
            ax.set_ylabel('Scaled amplitude [arbitrary units]')
            ax.legend(loc='best')
            plot2 = '%s_COMPARISON-%s.png' % (channelstub, gpsstub)
            try:
                plot.save(plot2)
            except (IOError, IndexError):
                plot.save(plot2)
            except RuntimeError as e:
                if 'latex' in str(e).lower():
                    plot.save(plot2)
                else:
                    raise
            plot.close()

            # plot scatter plots
            rangeColor = 'red'
            darmblrmsColor = 'blue'

            tsCopy = ts.reshape(-1, 1)
            rangetsCopy = rangets.reshape(-1, 1)
            darmblrmsCopy = darmblrms.reshape(-1, 1)

            darmblrmsReg = linear_model.LinearRegression()
            darmblrmsReg.fit(tsCopy, darmblrmsCopy)
            darmblrmsFit = darmblrmsReg.predict(tsCopy)

            rangeReg = linear_model.LinearRegression()
            rangeReg.fit(tsCopy, rangetsCopy)
            rangeFit = rangeReg.predict(tsCopy)

            fig = Plot(figsize=(12, 6))
            fig.subplots_adjust(*p2)
            ax = fig.add_subplot(121)
            ax.set_xlabel('Channel units')
            ax.set_ylabel('Sensitive range [Mpc]')
            yrange = abs(max(darmblrms.value) - min(darmblrms.value))
            upperLim = max(darmblrms.value) + .1 * yrange
            lowerLim = min(darmblrms.value) - .1 * yrange
            ax.set_ylim(lowerLim, upperLim)
            ax.text(.9, .1, 'r = ' + str('{0:.2}'.format(corr1)),
                    verticalalignment='bottom', horizontalalignment='right',
                    transform=ax.transAxes, color='black', size=20,
                    bbox=dict(boxstyle='square', facecolor='white', alpha=.75,
                              edgecolor='black'))
            fig.add_scatter(ts, darmblrms, color=darmblrmsColor)
            fig.add_line(ts, darmblrmsFit, color='black')

            ax = fig.add_subplot(122)
            ax.set_xlabel('Channel units')
            ax.set_ylabel('$h(t)$ BLRMS [strain]')
            ax.text(.9, .1, 'r = ' + str('{0:.2}'.format(corr2)),
                    verticalalignment='bottom', horizontalalignment='right',
                    transform=ax.transAxes, color='black', size=20,
                    bbox=dict(boxstyle='square', facecolor='white', alpha=.75,
                              edgecolor='black'))
            fig.add_scatter(ts, rangets, color=rangeColor)
            fig.add_line(ts, rangeFit, color='black')

            plot3 = '%s_SCATTER-%s.png' % (channelstub, gpsstub)
            try:
                fig.save(plot3)
            except (IOError, IndexError):
                fig.save(plot3)
            except RuntimeError as e:
                if 'latex' in str(e).lower():
                    fig.save(plot3)
                else:
                    raise
            plt.close(fig)

        # increment counter and print status
        with counter.get_lock():
            counter.value += 1
            pc = 100 * counter.value / nchan
            LOGGER.debug("Completed [%d/%d] %3d%% %-50s"
                         % (counter.value, nchan, pc, '(%s)' % str(chan)))
            sys.stdout.flush()
        return chan, corr1, corr2, plot1, plot2, plot3, corr1s, corr2s

    pool = multiprocessing.Pool(nprocplot)
    results = pool.map(process_channel, list(auxdata.items()))
    results.sort(key=lambda x: (x[1] is not None and max(abs(x[1]), abs(x[2]),
                 abs(x[6]), abs(x[7])) or 0, x[0]), reverse=True)

    with open('results.txt', 'w') as f:
        for ch, corr1, corr2, _, _, _, corr1s, corr2s in results:
            print('%s %s %s %s %s' % (
                ch, corr1, corr2, corr1s, corr2s), file=f)

    # -- write html
    trange = '%d-%d' % (start, end)
    title = '%s Slow Correlations: %s' % (args.ifo, trange)
    links = [trange] + [(s, '#%s' % s.lower())
                        for s in ['Parameters', 'Results']]
    (brand, class_) = htmlio.get_brand(args.ifo, 'Correlations', start)
    navbar = htmlio.navbar(links, class_=class_, brand=brand)
    page = htmlio.new_bootstrap_page(title=title, navbar=navbar)

    # header
    if flower:
        pstr = ('<code>%s</code> (band-limited %s-%s Hz)'
                % (primary, flower, fupper))
    else:
        pstr = primary
    if args.trend_type == 'minute':
        pstr += ' and <code>%s</code>' % rangechannel
    page.div(class_='pb-2 mt-3 mb-2 border-bottom')
    page.h1(title)
    page.p("This analysis searched %d channels for linear correlations with %s"
           % (nchan, pstr))
    page.div.close()

    # run parameters
    contents = [
        ('Primary channel',
         '{} ({})'.format(
             primary, args.primary_frametype.format(ifo=args.ifo))),
        ('Range channel',
         '{} ({})'.format(rangechannel, args.range_frametype or '-')),
        ('Band-pass', '{}-{}'.format(flower, fupper))]
    page.add(htmlio.parameter_table(contents, start=start, end=end))

    # results
    page.h2('Results', class_='mt-4', id_='results')
    r_blrms = "<i>r<sub>blrms</sub> </i>"
    r_range = "<i>r<sub>range</sub> </i>"
    r = "<i>r</i>"
    rho_blrms = "<i>&rho;<sub>blrms</sub> </i>"
    rho_range = "<i>&rho;<sub>range</sub> </i>"
    rho = "<i>&rho;</i>"
    Pearson_wikilink = htmlio.markup.oneliner.a(
        "Pearson's correlation coefficient",
        href="https://en.wikipedia.org/wiki/"
             "Pearson_product-moment_correlation_coefficient",
        rel="external")
    numpylink = htmlio.markup.oneliner.a(
        "<code>numpy.corrcoef</code>",
        href="http://docs.scipy.org/doc/numpy-1.10.1/reference/generated/"
             "numpy.corrcoef.html",
        rel="external")
    Spearman_wikilink = htmlio.markup.oneliner.a(
        "Spearman's correlation coefficient",
        href="https://en.wikipedia.org/wiki/"
             "Spearman%27s_rank_correlation_coefficient",
        rel="external")
    scipylink = htmlio.markup.oneliner.a(
        "<code>scipy.stats.spearmanr</code>",
        href="http://docs.scipy.org/doc/scipy-0.14.0/reference/generated/"
             "scipy.stats.spearmanr.html",
        rel="external")
    page.p("In the results below, all %s values are calculated as"
           " the square of %s using %s and all %s values are calculated"
           " as the square of %s using %s."
           % (r, Pearson_wikilink, numpylink, rho,
              Spearman_wikilink, scipylink))
    if args.trend_type == 'minute':
        page.p("%s and %s are reported for <code>%s</code>."
               " %s and %s are reported for <code>%s</code>."
               " The %s between these two channels is %.2f."
               " The %s between these two channels is %.2f."
               % (r_blrms, rho_blrms, primary, r_range, rho_range,
                  rangechannel, r, corr_p, rho, corr_s))

    page.div(id_='accordion')
    for i, (ch, corr1, corr2, plot1, plot2, plot3,
            corr1s, corr2s) in enumerate(results):
        if corr1 is None:
            h = '%s [flat]' % ch
        elif plot1 is None:
            h = ('%s [%s = %.2f, %s = %.2f] [%s = %.2f, %s = %.2f]'
                 ' [below threshold]'
                 % (ch, r_blrms, corr1, r_range, corr2, rho_blrms,
                    corr1s, rho_range, corr2s))
        elif args.trend_type == 'minute':
            h = ('%s [%s = %.2f, %s = %.2f] [%s = %.2f, %s = %.2f]'
                 % (ch, r_blrms, corr1, r_range, corr2, rho_blrms,
                    corr1s, rho_range, corr2s))
        else:
            h = '%s [%s = %.2f]' % (ch, r_blrms, corr1)
        if (corr1 is None) or (corr1 == 0) or (plot1 is None):
            context = 'bg-light'
        elif ((numpy.absolute(corr1) >= .6) or (numpy.absolute(corr1s) >= .6)
              or (numpy.absolute(corr2) >= .6)
              or (numpy.absolute(corr2s) >= .6)):
            context = 'text-white bg-danger'
        elif ((numpy.absolute(corr1) >= .4) or (numpy.absolute(corr1s) >= .4)
              or (numpy.absolute(corr2) >= .4)
              or (numpy.absolute(corr2s) >= .4)):
            context = 'text-white bg-warning'
        else:
            context = 'text-white bg-info'
        page.div(class_='card %s' % context)
        # heading
        page.div(class_='card-header')
        page.a(h, class_='collapsed card-link cis-link', href='#channel%d' % i,
               **{'data-toggle': 'collapse'})
        page.div.close()  # card-header
        # body
        page.div(id_='channel%d' % i, class_='collapse',
                 **{'data-parent': '#accordion'})
        page.div(class_='card-body')
        if corr1 is None:
            page.p("The amplitude data for this channel is flat"
                   " (does not change) for the chosen time period.")
        elif plot1 is None:
            page.p("Niether r nor rho are above the threshold of %.2f."
                   % (args.threshold))
        else:
            for p in (plot1, plot2, plot3):
                img = htmlio.FancyPlot(p)
                page.add(htmlio.fancybox_img(img))
        page.div.close()  # card-body
        page.div.close()  # collapse
        page.div.close()  # card
    page.div.close()  # accordion
    htmlio.close_page(page, 'index.html')  # save and close

    LOGGER.info("-- Process Completed")


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
