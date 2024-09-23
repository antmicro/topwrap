# Topwrap

Copyright (c) 2021-2024 [Antmicro](https://antmicro.com)

Topwrap is an open source CLI & GUI toolkit for connecting individual HDL modules into full designs of varying complexity. The toolkit is designed to take advantage of the ever-growing availability of open source digital logic designs, and offers a user-friendly graphical interface which lets you mix-and-match GUI-driven design with CLI-based adjustments, and present designs in a diagram form.

Topwrap’s most notable features are:
* Parsing HDL design files with automatic recognition of common interfaces
* Simple YAML-based description for command-line use
* Capability to create a custom libraries for reuse across projects
* User-friendly GUI:

![GUI example](docs/source/img/soc-diagram-anim.gif)

## Installation

```bash
apt install -y git g++ make python3 python3-pip yosys npm
pip install .
```

More detailed instructions, and steps for non Debian distributions are available in the [installation guide](https://antmicro.github.io/topwrap/getting_started.html#installation).

## Capabilities

Topwrap offers functionalities in three main areas via the following commands:

* `topwrap parse` - automatically parses HDL modules and groups ports into interfaces to enable connecting them more conveniently in the design. This step is necessary, as it creates module description files for the parsed modules, which are used by Topwrap internally. These have a [documented format](https://antmicro.github.io/topwrap/description_files.html#ip-description-files) and can also be written and adjusted manually.
* `topwrap build` - generates the top level based on a design description file. It references files describing the HDL modules mentioned previously and describes all connections between them, external ports of the design, and, optionally, interconnects. To automate the project generation and build process, Topwrap can also generate e.g [FuseSoC](https://github.com/olofk/fusesoc) files to simplify work with Topwrap-made designs in other tools.
* `topwrap kpm_client` - spawns a [Pipeline Manager](https://github.com/antmicro/kenning-pipeline-manager) client to provide a convenient GUI for creating designs. It can be accessed in the browser and allows placing and connecting the HDL modules via dragging & dropping. After a design is finished, sanity checks and design building can be triggered from the GUI as well.

## Resources

Additional information, installation guide, tutorials, and example projects can be found in the [project documentation](https://antmicro.github.io/topwrap/introduction.html).

For implementation details check out the [developer's guide](https://antmicro.github.io/topwrap/developers_guide/setup.html).
