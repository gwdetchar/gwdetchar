#################
HTML construction
#################

.. currentmodule:: gwdetchar

Almost all the command-line tools bundled with GWDetChar are designed to produce nicely-formatted HTML output with custom CSS style formatting based on Twitter Bootstrap. The output pages are constructed programatically using `~MarkupPy` and a collection of custom python tools.

The :mod:`gwdetchar.io.html` module provides the following classes and functions:

.. autosummary::

   io.html.FancyPlot
   io.html.new_bootstrap_page
   io.html.navbar
   io.html.get_brand
   io.html.about_this_page
   io.html.get_command_line
   io.html.fancybox_img
   io.html.scaffold_plots
   io.html.table
   io.html.write_flag_html
   io.html.write_footer
   io.html.close_page

All output pages feature basic contextual information for that analysis, including the full command-line needed to reproduce it. For analyses that require configuration files (e.g., omega scans), a separate 'about' page is written that displays each configuration file used as well as a table of package versions installed in the environment at runtime.

The :mod:`gwdetchar.omega.html` module also provides functions specific to omega scan output pages:

.. autosummary::

   omega.html.wrap_html
   omega.html.toggle_link
   omega.html.write_summary_table
   omega.html.write_summary
   omega.html.write_ranking
   omega.html.write_block
   omega.html.write_qscan_page

For more information, please refer to these individual modules.
