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

Another module, :mod:`gwdetchar.cds`, is used to find mappings between front-end controllers.

======================
Command-line utilities
======================

.. note::

   These utilities require authentication with `LIGO.ORG` credentials for archived frame data access.

------------------
gwdetchar-overflow
------------------

The `gwdetchar-overflow` tool searches for overflows in a given time range over a given set of controllers from the front-end computing system. The simplest usage is as follows:

.. code-block:: bash

   gwdetchar-overflow -i <interferometer> <gps-start-time> <gps-end-time>

For example,

.. code-block:: bash

   gwdetchar-overflow -i H1 1126259442 1126259502

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: gwdetchar-overflow --help

-------------
gwdetchar-mct
-------------

Similarly, the `gwdetchar-mct` tool can be used to find times when any input signal crosses a given threshold:

.. command-output:: gwdetchar-mct --help
