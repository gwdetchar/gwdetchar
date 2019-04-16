#################
LASSO Correlation
#################

The least absolute shrinkage and selection operator (LASSO) is a regression technique using machine learning that tracks slow correlations among a large collection of time-domain data streams. For gravitational-wave detector characterisation, this technique is used to find correlations between environmental sensors and any noise in the primary strain channel.

.. currentmodule:: gwdetchar.lasso

The :mod:`gwdetchar.lasso` module provides the following functions:

.. autosummary::

   find_outliers
   remove_outliers
   fit
   find_alpha
   remove_flat
   remove_bad

The :mod:`gwdetchar.lasso.plot` module also provides functions for efficiently writing plots of LASSO data products:

.. autosummary::

   plot.configure_mpl
   plot.save_figure

====================
Command-line utility
====================

.. note::

   This utility requires authentication with `LIGO.ORG` credentials for archived frame data access.

---------------------------
gwdetchar-lasso-correlation
---------------------------

The `gwdetchar-lasso-correlation` tool searches for long, slow correlations between one channel identified as a primary (typically gravitational-wave strain) and several other (typically thousands of) auxiliary channels. For a full explanation of the available command-line arguments and options, you can run

.. command-output:: gwdetchar-lasso-correlation --help
