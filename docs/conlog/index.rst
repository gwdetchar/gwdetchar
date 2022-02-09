######
Conlog
######

============================
Channel Configuration Logger
============================

LIGO's real-time control loops are based on the Experimental Physics and Industrial Constrol System (EPICS), which at any given time is attempting to track the configuration in software of tens of thousands of data streams (or channels). The channel configuration logger, called Conlog, is a sophisticated system that identifies sudden changes by analyzing readback channels. The version of Conlog implemented here is scaled-back, simplified, and run in python on the command-line.

====================
Command-line utility
====================

.. note::

   This utility requires authentication with `LIGO.ORG` credentials for archived frame data access.

----------------
gwdetchar.conlog
----------------

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: python -m gwdetchar.conlog --help
