###########
Omega scans
###########

The :mod:`gwdetchar.omega` module provides a python implementation of the Omega gravitational-wave burst detection pipeline, used extensively for characterisation of transient noise in LIGO. This pipeline is designed around the `Q-transform`_ and is used to analyze hundreds of channels.

.. currentmodule:: gwdetchar.omega

The omega pipeline provides a 'scan' utility to make high-resolution Q-transform spectrograms of a configurable group of channels, to study the morphology and source of specific transient events (glitches).

The :mod:`gwdetchar.omega` module provides the following functions:

.. autosummary::

   highpass
   whiten
   conditioner
   primary
   cross_correlate
   scan

The :mod:`gwdetchar.omega.plot` module also provides functions for plotting omega scan data products:

.. autosummary::

   plot.timeseries_plot
   plot.spectral_plot
   plot.write_qscan_plots

======================
Command-line utilities
======================

GWDetChar provides two command-line utilities for running omega scans, taking care of data discovery and (optionally) configuration discovery for you.

.. note::

   For users working on any of the LIGO Data Grid (LDG) computer clusters, a standard set of configuration files are maintained and discoverable by default with `gwdetchar.omega`. For information about how to write custom configuration files, see the :mod:`gwdetchar.omega.config` module.

---------------
gwdetchar.omega
---------------

The :mod:`gwdetchar.omega` command-line interface is a Q-transform utility for generating omega scans. The simplest usage is as follows:

.. code-block:: bash

   python -m gwdetchar.omega -i `<interferometer>` `<gps-time>`

For example,

.. code-block:: bash

   python -m gwdetchar.omega -i L1 1126259461.5

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: python -m gwdetchar.omega --help

---------------------
gwdetchar.omega.batch
---------------------

To enable batch processing, :mod:`gwdetchar.omega.batch` is a wrapper around :mod:`gwdetchar.omega` that builds a workflow for executing multiple omega scans at once. This tool will generate a `Condor <https://research.cs.wisc.edu/htcondor/>`_ workflow (a Directed Acyclic Graph, or DAG) to process multiple event times either in parallel or in series.
The simplest usage is much the same as for :mod:`gwdetchar.omega`, but with multiple times:

.. code-block:: bash

   python -m gwdetchar.omega.batch -i `<interferometer>` `<gps-time-1>` `<gps-time-2>` `<gps-time-3>` `...`

Alternatively, you can pass all of the times in a single file:

.. code-block:: bash

   python -m gwdetchar.omega.batch -i L1 mytimes.txt

where `mytimes.txt` should contain a single column of GPS times.

For a full explanation of the available command-line interface and options, you can run

.. command-output:: python -m gwdetchar.omega.batch --help


.. _Q-transform: https://gwpy.github.io/docs/stable/examples/timeseries/qscan.html
