# Example projects

These example projects show some useful ways in which Topwrap can be used by the end-user.

:::{admonition} Information about embedded GUI
:class: note

This section extensively uses an embedded version of Topwrap's GUI, [Kenning Pipeline Manager](kenning-pipeline-manager), to visualize the design of all the examples.

You can use it to freely explore the entire design, add new blocks, connections, nodes and hierarchies.
You cannot however use features that require direct connection with the Topwrap's backend.
These features include, among others:

- Saving and loading data from/to `.yaml` files
- Verifying designs
- Building designs
:::

:::{tip}
Don't forget to use the "Enable fullscreen" button if the viewport feels too small!
```{image} img/kpm_button_fullscreen.png
```
:::

## Constant

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/constant)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_constant.json
:dataflow: ../build/kpm_jsons/data_constant.json
```

There is often a need to pass constant values to input ports of some IP Cores.
This example shows how easy expressing that is in the GUI and correspondingly, in the design description file (`project.yml`).

:::{tip}
You can find the constant node blueprint in the Nodes browser under the `Metanode` section.
:::

### Usage

**Enter the example's directory**
```bash
cd examples/constant
```

**Generate HDL source**

```bash
make generate
```


## Inout

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/inout)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_inout.json
:dataflow: ../build/kpm_jsons/data_inout.json
```

This example showcases the usage of an inout port and the way it's represented in the GUI.

:::{tip}
An inout port is denoted in the GUI by a green circle without a directional arrow inside.
:::

The design consists of 3 modules: input buffer `ibuf`, output buffer `obuf`, and bidirectional buffer `iobuf`.
Their operation can be described as:
* input buffer is a synchronous D-type flip flop with an asynchronous reset
* output buffer is a synchronous D-type flip flop with an asynchronous reset and an `output enable`, which sets output to high impedance state (Hi-Z)
* inout buffer instantiates 1 input and 1 output buffer. Input of the `ibuf` and output of the `obuf` are connected with an inout wire (port).

### Usage

**Enter the example's directory**
```bash
cd examples/inout
```

:::{admonition} Install required dependencies
:class: note

```bash
pip install -r requirements.txt
```
:::

**Generate bitstream for Zynq**

```bash
make
```

**Generate HDL sources without implementation**

```bash
make generate
```

## User repository

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/user_repository)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_user_repository.json
:dataflow: ../build/kpm_jsons/data_user_repository.json
```

This example presents a structure of a user repository containing prepackaged IP cores with sources and custom interface definitions, the design file and the config file.
Elements of the `repo` directory can be easily reused in different designs as long as you point to it either in the config file or in the CLI.

:::{seealso}
For more information about user repositories see [](user_repositories.md).
:::

:::{tip}
Because other components of the design are automatically imported from the repository, it's possible to load the entire example by specifying just the design file:
```bash
topwrap kpm_client -d project.yml
```
:::

### Usage

Build and run Pipeline Manager server

```bash
python -m topwrap kpm_build_server
python -m topwrap kpm_run_server
```

Navigate to `/examples/user_repository/` directory and run:

```bash
python -m topwrap kpm_client -d project.yml
```

Connect to the web GUI frontend in your browser on `http://127.0.0.1:5000`.

**Expected result**

Topwrap will load two cores from the `cores` directory that use an interface from the `interfaces` directory.

In the Nodes browser under `IPcore`, two loaded cores: `core1` and `core2`, should be visible.


## Hierarchy

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/hierarchy)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_hierarchy.json
:dataflow: ../build/kpm_jsons/data_hierarchy.json
```

This example shows how to create a hierarchical design in Topwrap.
It includes a hierarchy containing some IP cores and other nested hierarchies.

Check out `project.yml` to learn how does the above design translate to a [design description file](description_files.md)

:::{seealso}
For more information about hierarchies see [hierarchies docs](hierarchies).
:::

:::{tip}
Hierarchies are represented in the GUI by nodes with a green header.

You can display their inner designs by clicking the `Edit subgraph` option from the right click menu.

To exit from the hierarchy subgraph, find the back arrow button in the top left.


To add a new hierarchy node use the `New Graph Node` option in the node browser!
:::

### Usage
This example contains [user repo](https://antmicro.github.io/topwrap/user_repositories.html) (`repo` directory) and a configuration file for topwrap (`topwrap.yaml`) so it can be loaded by running
```
python -m topwrap kpm_client -d project.yml
```
in this example's directory.


## PWM

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/pwm)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_pwm.json
:dataflow: ../build/kpm_jsons/data_pwm.json
```

:::{tip}
The IP Core in the center of the design (`axi_axil_adapter`) showcases how IP Cores with overridable parameters are represented in the GUI.
:::

This is an example of an AXI-mapped PWM IP Core that can be generated with LiteX being connected to the ZYNQ Processing System.
The Core uses AXILite interface, so a proper `AXI -> AXILite` converter is needed.
You can access its registers starting from address `0x4000000` (that's the base address of `AXI_GP0` on ZYNQ).
The generated signal can be used in FPGA or connected to a physical port on a board.

:::{note}
To connect the I/O signals to specific FPGA pins, you need proper mappings in a constraints file. See `zynq.xdc` used in the setup and modify it accordingly.
:::

### Usage

**Enter the example's directory**
```bash
cd examples/pwm
```

:::{admonition} Install required dependencies
:class: note

```bash
pip install -r requirements.txt
```

In order to be able to generate a bitstream you also need to install Vivado and add it to your `PATH`.
:::

**Generate bitstream for Zynq**

```bash
make
```

**If you wish to generate HDL sources without running Vivado, you can use**

```bash
make generate
```



## HDMI

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/hdmi)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_hdmi.json
:dataflow: ../build/kpm_jsons/data_hdmi.json
```

This is an example on how to use Topwrap to build a complex, synthesizable design.

### Usage

**Enter the example's directory**
```bash
cd examples/hdmi
```

:::{admonition} Install required dependencies
:class: note

```bash
pip install -r requirements.txt
```

In order to be able to generate a bitstream you also need to install Vivado and add it to your `PATH`.
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

**If you wish to generate HDL sources without running Vivado, you can use**

```bash
make generate
```



## SoC

[Link to source](https://github.com/antmicro/topwrap/tree/main/examples/soc)

```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_soc.json
:dataflow: ../build/kpm_jsons/data_soc.json
```

This is an example on how to use Topwrap to build a synthesizable SoC design.
The SoC contains a VexRiscv core, data and instruction memory, UART and interconnect that ties all components together.

### Usage

**Enter the example's directory**
```bash
cd examples/soc
```

:::{admonition} Install required dependencies
:class: note

```bash
sudo apt install git make g++ ninja-build gcc-riscv64-unknown-elf bsdextrautils
```

To run the simulation you also need:
- verilator

To create and load bitstream you also need:
- vivado (preferably version 2020.2)
- openFPGALoader ([this branch](https://github.com/antmicro/openFPGALoader/tree/antmicro-ddr-tester-boards))
:::


**Generate HDL sources**

```bash
make generate
```

**Build and run simulation**

```bash
make sim
```

Expected waveform generated by the simulation is shown in `expected-waveform.svg`.

**Generate bitstream**

```bash
make bitstream
```
