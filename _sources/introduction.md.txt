# Introduction

ASIC and FPGA designs consist of distinct blocks of logic bound together by a top-level design. 
To take advantage of this modularity and enable reuse of blocks across designs and so facilitate the shift towards automation in logic design, it is necessary to derive a generic way to aggregate the blocks in various configurations and make the top-level design easy to parse and process automatically.

Topwrap is an open source command line toolkit for connecting individual HDL modules into full designs of varying complexity.
The toolkit is designed to take advantage of the ever-growing availability of open source digital logic designs and offers a user-friendly graphical interface which lets you mix-and-match GUI-driven design with CLI-based adjustments and present designs in a diagram form thanks to the integration with Antmicro’s [Pipeline Manager](https://github.com/antmicro/kenning-pipeline-manager).

Topwrap's most notable features are:
* User-friendly GUI
* Parsing HDL design files with automatic recognition of common interfaces
* Simple YAML-based description for command-line use
* Capability to create custom libraries for reuse across projects
