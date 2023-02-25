#################
ADC/DAC overflows
#################

The LIGO real-time controls system is a sophisticated collection of control loops designed to hold the arm cavities in resonance. At fairly regular intervals, this system can experience overflows in digital-to-analogue (DAC) and analogue-to-digital (ADC) conversion, which we can keep track of using a few command-line tools.

.. currentmodule:: gwdetchar.daq

The :mod:`gwdetchar.daq` module provides the following functions:

.. autosummary::

   find_overflows
   find_overflow_segments
   ligo_accum_overflow_channel
   ligo_model_overflow_channels
   find_crossings

Another module, :mod:`gwdetchar.cds`, is used to find mappings between front-end data collection units.

======================
Command-line utilities
======================

.. note::

   These utilities require authentication with `LIGO.ORG` credentials for archived frame data access.

------------------
gwdetchar.overflow
------------------

The :mod:`gwdetchar.overflow` command-line interface searches for overflows in a given time range over a given set of data collection unit identifiers (DCUIDs) from the front-end computing system. The simplest usage is as follows:

.. code-block:: bash

   python -m gwdetchar.overflow -i `<interferometer>` `<gps-start-time>` `<gps-end-time>` `<DCUIDs>`

For example,

.. code-block:: bash

   python -m gwdetchar.overflow -i H1 1126259442 1126259502 8 10 19 29 30 88 97 98

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: python -m gwdetchar.overflow --help

-------------
gwdetchar.mct
-------------

Similarly, the :mod:`gwdetchar.mct` tool can be used to find times when any input signal crosses a given threshold:

.. command-output:: python -m gwdetchar.mct --help
