.. GWDetChar documentation master file, created by
   sphinx-quickstart on Mon Apr 15 20:43:29 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

############################################
Gravitational-wave Detector Characterisation
############################################

|PyPI version| |Conda version|

|DOI| |License| |Supported Python versions|

GWDetChar is a python package for gravitational-wave detector
characterisation and data quality. It is designed for use with ground-based
interferometric detectors such as the Laser Interferometer Gravitational-wave
Observatory (LIGO), Virgo, and GEO600.

To get started, simply import the core module:

.. code:: python

   import gwdetchar


============
Installation
============

GWDetChar is best installed with `conda`_:

.. code:: bash

   conda install -c conda-forge gwdetchar

but can also be installed with `pip`_:

.. code:: bash

   python -m pip install gwdetchar

Note, users with `LIGO.ORG` credentials have access to a software
container with a regularly-updated build of GWDetChar. For more
information please refer to the
`LSCSoft Conda <https://docs.ligo.org/lscsoft/conda/>`_ documentation.


============
Contributing
============

All code should follow the Python Style Guide outlined in `PEP 0008`_;
users can use the `flake8`_ package to check their code for style issues
before submitting.

See `the contributions guide`_ for the recommended procedure for
proposing additions/changes.

The GWDetChar project is hosted on GitHub:

* Issue tickets: https://github.com/gwdetchar/gwdetchar/issues
* Source code: https://github.com/gwdetchar/gwdetchar


License
-------

GWDetChar is distributed under the `GNU General Public License`_.


.. toctree::
   :maxdepth: 1
   :hidden:

   daq/index
   saturation/index
   lasso/index
   scattering/index
   omega/index
   conlog/index
   html/index
   data/index
   nagios/index
   api/index


.. _PEP 0008: https://www.python.org/dev/peps/pep-0008/
.. _flake8: http://flake8.pycqa.org
.. _the contributions guide: https://github.com/gwdetchar/gwdetchar/blob/master/CONTRIBUTING.md
.. _conda: https://conda.io
.. _pip: https://pip.pypa.io/en/stable/
.. _GNU General Public License: https://github.com/gwdetchar/gwdetchar/blob/master/LICENSE


.. |PyPI version| image:: https://badge.fury.io/py/gwdetchar.svg
   :target: http://badge.fury.io/py/gwdetchar
.. |Conda version| image:: https://img.shields.io/conda/vn/conda-forge/gwdetchar.svg
   :target: https://anaconda.org/conda-forge/gwdetchar/
.. |DOI| image:: https://zenodo.org/badge/36960054.svg
   :target: https://zenodo.org/badge/latestdoi/36960054
.. |License| image:: https://img.shields.io/pypi/l/gwdetchar.svg
   :target: https://choosealicense.com/licenses/gpl-3.0/
.. |Supported Python versions| image:: https://img.shields.io/pypi/pyversions/gwdetchar.svg
   :target: https://pypi.org/project/gwdetchar/
