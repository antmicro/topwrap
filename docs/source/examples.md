# Sample projects

These projects demonstrate how to use Topwrap on a practical level, with examples based on a variety of useful designs.

## Embedded GUI

This section extensively uses an embedded version of [Topwrap's GUI](https://github.com/antmicro/kenning-pipeline-manager) to visualize the design of all the examples.

You can use it to explore designs, while adding new blocks, connections, nodes and hierarchies.

The features that require direct connection with Topwrap's backend are not implemented in this demo version, including:

- saving and loading data in `.yaml` files
- building designs
- verifying designs


:::{tip}
Don't forget to use the "Enable fullscreen" button if the viewport is too small.

```{image} img/kpm_button_fullscreen.png
```

:::

## Constant

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/constant)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_constant.json
:dataflow: ../build/kpm_jsons/data_constant.json
```

This example shows how to assign a constant value to a port in an IP core. You can see it in the GUI by using the interactive preview functionality.
It is also visible in the description file (`project.yaml`).

:::{tip}
You can find the constant node blueprint in the nodes browser within the `Metanode` section.
:::

### Usage

Switch to the subdirectory with the example:

```bash
cd examples/constant
```

Generate the HDL source:

```bash
make generate
```

## Inout

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/inout)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_inout.json
:dataflow: ../build/kpm_jsons/data_inout.json
```

This example showcases the usage of an inout port and its representation in the GUI.

:::{tip}
An inout port is marked in the GUI by a green circle without a directional arrow inside.
:::

The design consists of 3 modules: input buffer `ibuf`, output buffer `obuf`, and bidirectional buffer `iobuf`.
Their operation can be described as:

* the input buffer is a synchronous D-type flip flop with an asynchronous reset
* the output buffer is a synchronous D-type flip flop with an asynchronous reset and an `output enable`, which sets the output to a high impedance state (Hi-Z)
* the inout buffer instantiates 1 input and 1 output buffer. The input of the `ibuf` and output of the `obuf` are connected with an inout wire (port).

### Usage

Switch to the subdirectory with the example:

```bash
cd examples/inout
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

:::

To generate the bitstream for Zynq, use:

```bash
make
```

To generate only the HDL sources use:

```bash
make generate
```

## User repository

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/user_repository)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_user_repository.json
:dataflow: ../build/kpm_jsons/data_user_repository.json
```

This example presents the structure of a user repository containing prepackaged IP cores with sources and custom interface definitions.

Elements of the `repo` directory can be easily reused in different designs by linking to them from the config file or in the CLI.

:::{seealso}
For more information about user repositories see [this chapter](user_repositories.md).
:::

:::{tip}
As other components of the design are automatically imported from the repository, it's possible to load the entire example by specifying the design file:

```bash
topwrap gui -d project.yml
```

:::

### Usage

Navigate to the `/examples/user_repository/` directory and run:

```bash
topwrap gui -d project.yml
```

**Expected result**

Topwrap will load two cores from the `cores` directory, using the interface from the `interfaces` directory.

In the Nodes browser under `IPcore`, two loaded cores: `core1` and `core2`, should be visible.

## Hierarchy

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/hierarchy)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_hierarchy.json
:dataflow: ../build/kpm_jsons/data_hierarchy.json
```

This example shows how to create a hierarchical design in Topwrap, including a hierarchy that contains IP cores as well as other nested hierarchies.

Check out `project.yaml` to learn how the above design translates to a [design description file](description_files.md)

:::{seealso}
For more information, see the section on [Hierarchies](description_files.md#hierarchies).
:::

:::{tip}
Hierarchies are represented in the GUI by nodes with a green header. To display inner designs, click the `Edit subgraph` option from the context menu.

To exit from the hierarchy subgraph, use the back arrow button on the top left.
To add a new hierarchy node, use the `New Graph Node` option in the node browser.
:::

### Usage

This example contains the [user repository](https://antmicro.github.io/topwrap/user_repositories.html) (`repo` directory) and a configuration file for Topwrap (`topwrap.yaml`). It can be loaded by entering the examples directory, and running:

```
topwrap gui -d project.yaml
```

## PWM

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/pwm)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_pwm.json
:dataflow: ../build/kpm_jsons/data_pwm.json
```

:::{tip}
The IP core in the center of the design (`axi_axil_adapter`) showcases how IP cores with overridable parameters are represented in the GUI.
:::

This is an example of an AXI-mapped PWM IP core that can be generated with LiteX, connected to the ZYNQ Processing System.
The core uses the AXILite interface, so a `AXI -> AXILite` converter is needed.
You can access its registers starting from address `0x4000000` (the base address of `AXI_GP0` on ZYNQ).
The generated signal can be used in a FPGA or connected to a physical port on a board.

:::{note}
To connect I/O signals to specific FPGA pins, you must use mappings in a constraints file. See `zynq.xdc` used in the setup and modify it accordingly.
:::

### Usage

Switch to the subdirectory with the example:

```bash
cd examples/pwm
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

:::{note}
In order to generate a bitstream, install [Vivado](https://www.xilinx.com/support/download.html) and add it to the `PATH`.
:::

To generate bitstream for Zynq, use:

```bash
make
```

To generate HDL sources without running Vivado, use:

```bash
make generate
```

## HDMI

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/hdmi)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_hdmi.json
:dataflow: ../build/kpm_jsons/data_hdmi.json
```

This is an example of how to use Topwrap to build a complex and synthesizable design.

### Usage

Switch to the subdirectory with the example:

```bash
cd examples/hdmi
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

:::{note}
In order to generate a bitstream, install Vivado and add it to the `PATH`.
:::

**Generate bitstream for desired target**

Snickerdoodle Black:

```bash
make snickerdoodle
```

Zynq Video Board:

```bash
make zvb
```

To generate HDL sources without running Vivado, use:

```bash
make generate
```

## SoC

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/soc)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_soc.json
:dataflow: ../build/kpm_jsons/data_soc.json
```

This is an example of how to use Topwrap to build a synthesizable SoC design.
The SoC contains a VexRiscv core, data and instruction memory, UART and an interconnect that ties all the components together.

### Usage

Switch to the subdirectory with the example:

```bash
cd examples/soc
```

Install the required dependencies:

```bash
sudo apt install git make g++ ninja-build gcc-riscv64-unknown-elf bsdextrautils
```

:::{note}
To run the simulation, you need:

- verilator

To create and load the bitstream, use:

- [Vivado](https://www.xilinx.com/support/download.html) (preferably version 2020.2).
- openFPGALoader ([branch](https://github.com/antmicro/openFPGALoader/tree/antmicro-ddr-tester-boards))
:::

Generate HDL sources:

```bash
make generate
```

Build and run the simulation:

```bash
make sim
```

The expected waveform generated by the simulation is shown in `expected-waveform.svg`.

Generate the bitstream:

```bash
make bitstream
```
