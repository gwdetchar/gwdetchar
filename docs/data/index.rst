#########################
Access to LIGO/Virgo data
#########################

.. currentmodule:: gwdetchar.io.datafind

Users with `LIGO.ORG` credentials are freely able to access all archived data either from local gravitational-wave frame files or over an NDS server. The :mod:`gwdetchar.io.html` module is designed to simplify this process for scripting, and provides the following functions:

.. autosummary::

   check_flag
   remove_missing_channels
   get_data

Note, in most cases, calls to :func:`gwdetchar.io.datafind.get_data` that are unable to read from a local source will automatically fall back to NDS. For users who wish to run omega scans over publicly available data, please refer to :mod:`gwdetchar.omega.config`.

For more information about data access, please see `GWpy <https://gwpy.github.io/docs/stable/timeseries/remote-access.html>`_.
