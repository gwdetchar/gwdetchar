##################
Optical scattering
##################

The :mod:`gwdetchar.scattering` module provides a suite of tools designed to look for evidence of optical scattering in the LIGO detectors. This tool finds the velocity of a set of optics as measured by optical position sensors and electromagnetic drivers (OSEMs), then compares against the wavelength of a carrier laser to estimate the fringe frequency. For more information about this method, please see `Accadia et al. (2010) <http://iopscience.iop.org/article/10.1088/0264-9381/27/19/194011>`_.

.. currentmodule:: gwdetchar.scattering

The :mod:`gwdetchar.scattering` module provides the following functions:

.. autosummary::

   get_fringe_frequency

.. note::

   OSEMs directly measure only the translational (linear) motion of optics, typically on the scale of microns. To measure velocity, :mod:`gwdetchar.scattering` uses a `Savitzky-Golay filter <https://en.wikipedia.org/wiki/Savitzky–Golay_filter>`_ to take smoothed time derivatives.

The :mod:`gwdetchar.scattering.plot` module also provides functions for comparing fringe frequency projections against high-resolution Q-transform spectrograms:

.. autosummary::

   plot.spectral_comparison
   plot.spectral_overlay

======================
Command-line utilities
======================

GWDetChar provides two command-line utilities for optical scattering; one is designed to identify time periods when scattering is likely, the other compares projected fringe frequencies against a high-resolution spectrogram of gravitational-wave strain.

.. note::

   These utilities require authentication with `LIGO.ORG` credentials for archived frame data access.

--------------------
gwdetchar.scattering
--------------------

The :mod:`gwdetchar.scattering` command-line interface searches over a standard list of OSEM measurements within a user-specified time range for evidence of optical scattering. The simplest usage is as follows:

.. code-block:: bash

   python -m gwdetchar.scattering -i `<interferometer>` `<gps-start-time>` `<gps-end-time>`

For example,

.. code-block:: bash

   python -m gwdetchar.scattering -i H1 1126259442 1126259502

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: python -m gwdetchar.scattering --help

---------------------------
gwdetchar.scattering.simple
---------------------------

The :mod:`gwdetchar.scattering.simple` can also be run as a command-line module to compare fringe frequency projections against gravitational-wave strain at a specific time. The simplest usage is similar to :mod:`gwdetchar.scattering`, but with only a single time:

.. code-block:: bash

   python -m gwdetchar.scattering.simple -i `<interferometer>` `<gps-time>`

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: python -m gwdetchar.scattering.simple --help
