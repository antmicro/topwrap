(getting-started)=
# Getting started

The purpose of this chapter is to provide a step by step guide on how to create a simple design with Topwrap.

All the necessary files needed to follow this guide are in the `examples/getting_started_demo` directory.

:::{admonition} Important
:class: attention
If you haven't installed Topwrap yet, go to the [Installation chapter](installation.md) and make sure to install the additional dependencies for `topwrap parse`.
:::

(getting-started-design-overview)=
## Design overview

We are going to create a design that will be visually represented in an [interactive GUI](https://antmicro.github.io/topwrap/usage.html#gui), as seen below.

```{kpm_iframe}
:spec: ../../examples/getting_started_demo/kpm/specification.json
:dataflow: ../../examples/getting_started_demo/kpm/dataflow.json
```

It consists of two cores: `simple_core_1` and `simple_core_2` that connect to each other and to an external input/output.

:::{note}
Metanodes are always utilized in designs to represent external input/output ports, module hierarchy ports or constant values.
They can be found in the "Metanode" section.
:::

(getting-started-parsing-verilog)=
## Parsing Verilog files

The first step when creating designs is to parse Verilog files into [IP core description YAMLs](https://antmicro.github.io/topwrap/usage.html#generating-ip-core-description-yamls) that are understood by Topwrap.

In the `verilogs` directory, there are two Verilog files described, `simple_core_1` and `simple_core_2`.

To generate the IP core descriptions from these Verilog files run:

```bash
topwrap parse verilogs/{simple_core_1.v,simple_core_2.v}
```

Topwrap will generate two files `gen_simple_core_1.yaml` and `gen_simple_core_2.yaml` that represent the corresponding Verilog files.

(getting-started-building-designs)=
## Building designs with Topwrap

(getting-started-building-creating-designs)=
### Creating the design

The generated IP core YAMLs can be loaded into the GUI.

Run the GUI client:
```bash
topwrap gui gen_simple_core_1.yaml gen_simple_core_2.yaml
```
It should build and start server, connect the client to it and open the browser with GUI.

The loaded IP cores can be found in the IPcore section:

```
{image} img/side_bar_kpm.png
```

With these IP cores and default metanodes, you can easily create designs by dragging and connecting the cores.

Let's make the design from the demo in the introduction.

```
{image} img/getting_started_project.png
```

:::
{note} You can change the name of an individual node by right clicking on it and selecting `rename`. This is useful when creating multiple instances of the same IP core.
:::

You can save the project in the [Design Description](description_files.md) format, which is used by Topwrap to represent the created design.

To do this, select the graph button and select `Save file`.

```
{image} img/save_graph_kpm.png
```

:::{note}
The difference between `Save file` and `Save graph file` lies in which format is used for saving.

`Save file` will save the design description in the YAML format which Topwrap uses.

`Save graph file` will save the design in the [graph JSON format](https://antmicro.github.io/kenning-pipeline-manager/specification-format.html) which the GUI uses. You should only choose this one if you have a specific custom layout of the nodes in the design and you want to save it.
:::

(getting-started-building-designs-generating-verilog)=
### Generating Verilog in the GUI

You can generate Verilog from the design created in the previous section if you have the example running as described in the previous section. On the top bar, these four buttons are visible:

```
{image} img/kpm_buttons.png
```

1. Save/Load designs.
2. Toggle the node browser.
3. Validate the design.
4. Build the design. If it does not contain errors, a top module will be created in the directory where `topwrap kpm_client` was run.

(getting-started-command-line-flow)=
## Command-line flow
(getting-started-command-line-flow-creating-designs)=
### Creating designs

The manual creation of designs requires familiarity with the [Design Description](description_files.md) format.

First, include all the IP core files needed in the `ips` section.

```yaml
ips:
  simple_core_1:
    file: gen_simple_core_1.yaml
  simple_core_2:
    file: gen_simple_core_2.yaml
```

Here, the name of the node is declared, and the IP core `gen_simple_core_1.yaml` is named `simple_core_1` in the GUI.

Now we can start creating the design under the `design` section. The design doesn't have any parameters set, so we can skip this part and go straight into the `ports` section. In there, the connections between IP cores are defined. In the demo example, there is only one connection - between `gen_simple_core_1` and `gen_simple_core_2`.

In our design, it is represented like this:

```yaml
design:
  ports:
    simple_core_2:
      a:
      - simple_core_1
      - z
```

Notice that `input` is connected to `output`.
All that is left to do is to declare the external connections to metanodes, like this:

```yaml
external:
  ports:
    in:
    - rst
    - clk
    out:
    - Output_y
    - Output_c
```

Now connect them to IP cores.

```yaml
design:
  ports:
    simple_core_1:
      clk: clk
      rst: rst
    simple_core_2:
      a:
      - simple_core_1
      - z
      c: Output_c
      y: Output_y
```

The final design:

```yaml
ips:
  simple_core_1:
    file: gen_simple_core_1.yaml
  simple_core_2:
    file: gen_simple_core_2.yaml
design:
  ports:
    simple_core_1:
      clk: clk
      rst: rst
    simple_core_2:
      a:
      - simple_core_1
      - z
      c: Output_c
      y: Output_y
external:
  ports:
    in:
    - rst
    - clk
    out:
    - Output_y
    - Output_c
```

(getting-started-command-line-flow-generating-verilog-top-files)=
### Generating Verilog top files

:::{info}
Topwrap uses [Amaranth](https://github.com/amaranth-lang/amaranth) for generating Verilog top files.
:::

To generate the top file, use `topwrap build` and provide the design.

To do this, ensure you are in the `examples/getting_started_demo` directory and run:

```bash
topwrap build --design {design_name.yaml}
```

Where the `{design_name.yaml}` is the design saved at the end of the previous section.
The generated Verilog file can be found in the `/build` directory.

There will be a warning:

```
WARNING:root:You did not specify part number. 'None' will be used and thus your implementation may fail.
```

This is because the  `--part` flag was omitted since it's just a example, and is not for any specific FPGA chip.
For building custom designs, we recommend always specifying the `--part` flag.
