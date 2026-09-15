####################
Software saturations
####################

The LIGO real-time controls system is a sophisticated collection of control loops designed to hold the arm cavities in resonance, each control loop typically featuring a large number of digital filters. To avoid instability by accidentally actuating too strongly, many of these filter banks are assigned a set of hard limits in the front-end control software. We can keep track of times when those limits are saturated by analyzing the readback channels from filter banks.

.. currentmodule:: gwdetchar.saturation

The :mod:`gwdetchar.saturation` module provides the following functions:

.. autosummary::

   find_saturations
   grouper
   find_limit_channels
   is_saturated

====================
Command-line utility
====================

.. note::

   This utility requires authentication with `LIGO.ORG` credentials for archived frame data access.

--------------------
gwdetchar.saturation
--------------------

The :mod:`gwdetchar.saturation` command-line interface searches (typically several thousand) channels corresponding to control system filter banks, looking for times during which the `OUTPUT` channels match or exceed the `LIMIT` value set in control software. The simplest usage is as follows:

.. code-block:: bash

   python -m gwdetchar.saturation -i `<interferometer>` `<gps-start-time>` `<gps-end-time>`

For example,

.. code-block:: bash

   python -m gwdetchar.saturation -i L1 1126259442 1126259502

By default, the command searches all filter-bank channels with a ``_LIMIT``
channel and a matching ``_LIMEN`` or ``_SWSTAT`` channel. To restrict the
search, pass ``--channels`` a text file containing one base channel name per
line. Base names omit the ``_LIMIT``, ``_LIMEN``, ``_SWSTAT``, and ``_OUTPUT``
suffixes, for example:

.. code-block:: text

   L1:SUS-ITMX_M0_DAMP_L
   L1:SUS-ITMY_M0_DAMP_L

Then run:

.. code-block:: bash

   python -m gwdetchar.saturation -i L1 --channels channels.txt 1126259442 1126259502

Requested names that are not present in the frame data, or that do not have
the required limit and status channels, are ignored.

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: python -m gwdetchar.saturation --help
