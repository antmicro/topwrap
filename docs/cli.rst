Command-line Interface
======================

To run Topwrap, use::

    python -m fpga_topwrap --design project.yml

Where `project.yml` should be your file with description of the top module.

You can specify a directory to be scanned for additional sources::

    python -m fpga_topwrap --sources src --design project.yml

To get help, use::

    python -m fpga_topwrap --help
