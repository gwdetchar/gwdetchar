##########################
Service checks with Nagios
##########################

.. currentmodule:: gwdetchar.nagios

Nagios is an open source software application that can be used to monitor
automated infrastructure. As implemented for LIGO, the service works by
reading local JavaScript Object Notation (JSON) files containing status
updates written at runtime.

This python module provides an interface to writing status updates for Nagios,
intended for use by downstream consumers of GWDetChar. For live checks of
all LIGO service automation, see https://monitor.ligo.org.

Python module
=============

The :mod:`gwdetchar.nagios` module provides a simple utility for writing
a status file in JSON format that Nagios can parse:

.. autosummary::

   write_status

On the command-line
===================

If needed, Nagios status files can also be generated from the command-line:

.. command-output:: python -m gwdetchar.nagios --help
