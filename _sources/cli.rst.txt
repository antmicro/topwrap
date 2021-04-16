Command-line Interface
======================

To run Topwrap, use::

    python -m fpga_topwrap --design project.yml

Where `project.yml` should be your file with description of the top module.

You can specify a directory to be scanned for additional sources::

    python -m fpga_topwrap --sources src --design project.yml

To implement the design for a specific FPGA chip, provide the part name::

    python -m fpga_topwrap --sources src --design project.yml --part 'xc7z020clg400-3'

To get help, use::

    python -m fpga_topwrap --help
