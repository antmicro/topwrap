# Topwrap
[comment]: topwrap logo here?

Copyright (c) 2021-2024 [Antmicro](https://antmicro.com)

Topwrap is an [open source CLI & GUI toolkit](https://antmicro.com/blog/2024/08/parameterizable-digital-logic-design-with-the-topwrap-toolkit/) for connecting individual HDL modules into full designs of varying complexity. The toolkit is designed to take advantage of the ever-growing library of open source digital logic designs, and offers a user-friendly [graphical interface](https://github.com/antmicro/kenning-pipeline-manager) which lets users mix-and-match the GUI-driven design process with CLI-based fine adjustments for presenting designs in a diagram form.

Notable features include:
* [Parsing HDL design files](https://antmicro.github.io/topwrap/developers_guide/future_enhancements.html#provide-a-way-to-parse-hdl-sources-from-the-pipeline-manager-level) with automatic recognition of common interfaces
* Simple YAML-based descriptions for [command-line use](https://antmicro.github.io/topwrap/usage.html#generating-ip-core-description-yamls)
* Capability of creating custom libraries for reuse across projects
* The [user-friendly GUI](https://antmicro.github.io/topwrap/usage.html#gui)

![GUI example](docs/source/img/soc-diagram-anim.gif)

Topwrap allows users to build custom libraries of reusable modules, interfaces, and designs. It can assemble them all together and parametrize them to form top-level complete designs that can then be simulated, run in an FPGA or taped out. The designs themselves are human-readable in YAML format, allowing for easy reuse in multiple tools and projects while benefiting from being vendor-neutral. 

## Installation

To install on Debian-based distributions, use:

```bash
apt install -y git g++ make python3 python3-pip yosys npm
pip install .
```

More detailed instructions, as well as for non Debian-based distributions are available in the [installation guide](https://antmicro.github.io/topwrap/getting_started.html#installation).

## Functionality

Topwrap offers functionality in three main areas via the following commands:

* `topwrap parse` - automatically parses HDL modules and groups ports into interfaces to enable connecting them more conveniently in the design. 
* `topwrap build` - generates the top level based on a design description file. 
* `topwrap kpm_client` - spawns a [GUI](https://github.com/antmicro/kenning-pipeline-manager) for creating designs. 

## Resources

Additional information, example projects, tutorials and the developer's guide can be found in the [project documentation](https://antmicro.github.io/topwrap/introduction.html).