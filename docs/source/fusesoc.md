# FuseSoC

Toprwap uses FuseSoC to automate project generation and build process.

A `Core` file is needed in order to generate a project. The file can be generated from a template using {class}`FuseSocBuilder` class. The `Core` file contains information about source files and synthesis tools.

## Core file template

A template for the core file is bundled with Topwrap (`templates/core.yaml.j2`).
You may need to edit the file to change the backend tool, set additional `Hooks` and change the FPGA part name or other parameters.
By default, {class}`FuseSocBuilder` searches for the template file in the directory you work in, so you should first copy the template into the project's location.

## Using the FuseSocBuilder

Here's an example of how to generate a simple project:

```python
from fpga_topwrap.fuse_helper import FuseSocBuilder
fuse = FuseSocBuilder()

# add source of the IPs used in the project
fuse.add_source('DMATop.v', 'verilogSource')

# add source of the top file
fuse.add_source('top.v', 'verilogSource')

# specify the names of the Core file and the directory where sources are stored
# generate the project
fuse.build('build/top.core', 'sources')
```

Now you can run FuseSoC to generate bitstream and program FPGA:

```bash
fusesoc --cores-root build run project_1
```

This requires having the suitable backend tool in your `PATH` (Vivado, for example).
