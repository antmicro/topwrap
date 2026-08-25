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

The `verilogs` directory contains two Verilog files, `simple_core_1.v` and `simple_core_2.v`.

You can just import than into topwrap by having topwrap extract ports and other metadata:

```bash
topwrap package cores/simple_core_1.v -o cores/simple_core_1.yaml
topwrap package cores/simple_core_2.v -o cores/simple_core_2.yaml
```

Those yaml files can then be directly used in the topwrap design, you will find an example in `project.yaml`:

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

Here, `simple_core_1` and `simple_core_2` are directly referenced by their files.

Now we can start creating the design. The ports are wired up in `connections.ports` section. In there, the connections between IP cores are defined. In the demo example, there is only one connection - between `simple_core_1` and `simple_core_2`.

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

To generate IP-XACT 2022 files from a design, use `topwrap generate --ipxact`. The command schema is similar to `topwrap generate`:

```bash
topwrap generate --ipxact {design_name.yaml}
```

By default the generated files are written to the `build/src` directory. Change this with the `--build-dir` argument. Use `--iface-compliance` to force interface compliance checking.

See [Backends](backends.md#ipxactbackend) for details on the backend driving this command.

### Synthesis & FuseSoC

You can additionally generate a [FuseSoC core](#fusesoc) file during `topwrap build` to automate further synthesis and implementation by simply adding the `-f` (`--fuse`) option.

### Logging

Topwrap uses Python’s built-in `logging` module. By default, logging is configured with the `WARNING` level.
The default can be changed using the `--log-level` option:

```bash
topwrap --log-level DEBUG build --design {design_name.yaml}
```
