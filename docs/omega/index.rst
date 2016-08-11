###############
Omega utilities
###############

The :mod:`gwdetchar.omega` module provides utilities for processing data through, and understanding configurations for, the `Omega GW burst detection pipeline <https://trac.ligo.caltech.edu/omega/>`_, used extensively for characterisation of noise in LIGO.

===========
Omega scans
===========

.. currentmodule:: gwdetchar.omega.scan

The omega pipeline provides a 'scan' utility to make high-resolution Q-transform spectrograms of a configurable group of channels, to study the morphology and source of specific transient events (glitches).

:mod:`gwdetchar.omega.scan` provides the following helper functions/classes

.. autosummary::

   OmegaChannelList
   run

======================
Command-line utilities
======================

GWDetChar provides two command-line utilities for running omega scans, taking care of data discovery and (optionally) configuration discovery for you.

---
wdq
---

The `wdq` tool is a simple wrapper around the main `wpipeline scan` utility for generating Omega 'scans'. The simplest usage is as follows

.. code-block:: bash

   wdq <gps-time>

for example

.. code-block:: bash

   wdq 1126259461.5

For a full explanation of the available command-line argument and options, you can run

.. command-output:: wdq --help

---------
wdq-batch
---------

`wdq-batch` is a wrapper around `wdq` to build a workflow for executing multiple omega scans easily. This tool will generate both a `Condor <https://research.cs.wisc.edu/htcondor/>`_ workflow (a DAG), and a simple shell script (`.sh`) to process multiple times either in parallel or in series.
The simplest usage is much the same as for `wdq`, but with multiple times:

.. code-block:: bash

   wdq-batch <gps-time-1> <gps-time-2> <gps-time-3> ...

Alternatively, you can pass all of the times in a single file:

.. code-block:: bash

   wdq-batch mytimes.txt

where `mytimes.txt` should contain a single column of GPS times.

For a full explanation of the available command-line argument and options, you can run

.. command-output:: wdq-batch --help
