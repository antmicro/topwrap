# Getting started

The purpose of this chapter is to provide a step by step guide on how to create a simple design with Topwrap.
All the necessary files needed to follow this guide are in the [examples/getting_started_demo](https://github.com/antmicro/topwrap/tree/main/examples/getting_started_demo) directory.

:::{admonition} Important
:class: attention
If you haven't installed Topwrap yet, go to the [Installation chapter](#installation).
:::

## Design overview

We are going to create a design that will be visually represented in an [interactive GUI](https://antmicro.github.io/topwrap/usage.md#gui), as seen below.

```{pipeline_manager}
:spec: ../build/kpm_jsons/spec_getting_started_demo.json
:graph: ../build/kpm_jsons/data_getting_started_demo.json
```

It consists of two cores: `simple_core_1` and `simple_core_2` that connect to each other and to an external input/output.

:::{note}
Metanodes are always utilized in designs to represent external input/output ports, module hierarchy ports or constant values.
They can be found in the "Metanode" section.
:::

## Adding Verilog sources to repository

The `verilogs` directory contains two Verilog files, `simple_core_1.v` and `simple_core_2.v`. Topwrap can automatically sparsecan them and create the necessary topwrap files using `topwrap package`:

```bash
topwrap package cores/simple_core_1.v -o cores/simple_core_1.yaml
topwrap package cores/simple_core_2.v -o cores/simple_core_2.yaml
```

This is the most basic way of using topwrap, and we can now start building systems.

## Building designs with Topwrap

### Creating the design

The previously parsed source files can be loaded into the GUI with:

```bash
topwrap gui cores/simple_core_1.yaml cores/simple_core_2.yaml
```

The loaded IP cores can be found in the IPcore section:

```{image} img/side_bar_kpm.png
```

With these IP cores and default metanodes, you can easily create designs by dragging and connecting cores.

Let's make the design from the demo in the [introduction](#introduction).

```{image} img/getting_started_project.png
```

:::{note} You can change the name of an individual node by right clicking on it and selecting `rename`. This is useful when creating multiple instances of the same IP core.
:::

You can save the design using the `Save graph file` option from the menu.
This will create a [graph JSON format](https://antmicro.github.io/kenning-pipeline-manager/dataflow-format.html) file used by the GUI.
This is essentially a snapshot of everything that you created in the editor and can be loaded back later.

Alternatively, you can save the design into a [design description](description_files.md#design-description) YAML file by using the `Save file` option from the menu.
When using this option, in addition to downloading the design YAML file, Topwrap will also create an additional [positions YAML](description_files.md#positions-yaml) file describing the node positions.
This file, along with a copy of the design YAML, will be saved in a new subdirectory in the directory `topwrap gui` was run from.
The positions YAML file will be referenced from the saved design YAML file (via the `positions` property), and Topwrap will automatically attempt to load it next time you open the design.

### Generating Verilog in the GUI

You can generate Verilog from the design created in the previous section if you have the example running as described in the previous section. On the top bar, these four buttons are visible:

```{image} img/kpm_buttons.png
```

1. Save/Load designs.
2. Toggle the node browser.
3. Validate the design.
4. Build the design. If it does not contain errors, a top module will be created in the directory where `topwrap gui` was run.

## Command-line flow

### Creating designs

The manual creation of designs requires familiarity with the [Design Description](description_files.md#design-description) format.

First, include all the IP core files needed in the `ips` section.

```yaml
ips:
  simple_core_1:
    file: cores/simple_core_1.yaml
  simple_core_2:
    file: cores/simple_core_2.yaml
```

Now we can start creating the design by defining connections in the `connections.ports` section. In the demo example, there is only one connection - between `simple_core_1` and `simple_core_2`.

In our design, it is represented like this:

```yaml
connections:
  ports:
    simple_core_2:
      a: [simple_core_1, z]
```

All that is left to do is to declare external ports, like this:

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
connections:
  ports:
    simple_core_1:
      clk: clk
      rst: rst
    simple_core_2:
      a: [simple_core_1, z]
      c: Output_c
      y: Output_y
```

The final design:

```yaml
ips:
  simple_core_1:
    file: cores/simple_core_1.yaml
  simple_core_2:
    file: cores/simple_core_2.yaml
connections:
  ports:
    simple_core_1:
      clk: clk
      rst: rst
    simple_core_2:
      a: [simple_core_1, z]
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

### Generating Verilog top files

To generate the top file, use `topwrap generate` and provide the design. To do this, ensure you are in the `examples/getting_started_demo` directory and run:

```bash
topwrap generate {design_name.yaml}
```

Where `{design_name.yaml}` is the design saved at the end of the previous section. This will generate a `top.v` Verilog top wrapper in the specified build directory (`./build/src` by default).

### Generating IPXACT 2022 files

To generate IP-XACT 2022 files from a design, use `topwrap generate --ipxact`:

```bash
topwrap generate --ipxact {design_name.yaml}
```

By default the generated files are written to the `build/src` directory. Change this with the `--build-dir` argument. Use `--iface-compliance` to force interface compliance checking.

See [Backends](backends.md#ipxactbackend) for details on the backend driving this command.

### Synthesis & FuseSoC

You can additionally generate a [FuseSoC core](#fusesoc) file during `topwrap generate` to automate further synthesis and implementation by simply adding the `-f` (`--fuse`) option.

### Logging

Topwrap uses Python’s built-in `logging` module. By default, logging is configured with the `WARNING` level.
The default can be changed using the `--log-level` option:

```bash
topwrap --log-level DEBUG generate {design_name.yaml}
```

## Using libraries

So far, the IP cores in this guide were referenced directly by their YAML files with `file:`. Once you have cores you want to reuse across multiple designs or projects, it is more convenient to register them as a library and reference them by name with `core:` instead.

A library is a directory (or git repository) of CAPI2 `.core` files, as we are leveraging the FuseSoC package management infrastructure. To also add those extra files, just add `--lib` to `topwrap package`:

```bash
topwrap package --lib cores/simple_core_1.v -o cores/simple_core_1.yaml
topwrap package --lib cores/simple_core_2.v -o cores/simple_core_2.yaml
```

This writes `simple_core_1.core` and `simple_core_2.core` next to the YAML files, which is all that's needed to register the directory as a library:

```bash
topwrap library add mycores cores/
```

You can check what the registered library provides with:

```bash
topwrap library list all
```

With the library registered, a design can reference a module by name instead of a file path:

```yaml
ips:
  simple_core_1:
    core: simple_core_1
  simple_core_2:
    core: simple_core_2
```

The main advantage of libraries is sharing: since a library can be a git repository, a set of cores can be published once and reused across as many projects as needed, simply by registering the same URL wherever it is needed, instead of copying files around. In our example you would push the library into a repository and then use it:

```bash
topwrap library add antmicro https://github.com/antmicro.com/topwrap-cores
```

See the [Libraries](libraries.md) chapter for the full picture, including versioning and interface definitions.
