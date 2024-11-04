# Advanced options

This chapter builds upon the [Getting started](getting_started.md) chapter. If you haven't read it yet, it is recommended to do so first.

## Creating block design in the GUI

Upon successful connection to the server, Topwrap will generate and send to the server a specification describing the structure of previously selected IP cores. If the `-d` option is used, a design will be shown in the GUI. The content below is based on the PWM example located in `examples/pwm`. From there you can create or modify designs by:

* Adjusting IP cores' parameter values. Each node may have input boxes in which you can enter parameter values (default parameter values are added while adding an IP core to the block design):
```{image} img/node_parameters.png
```
Parameter values can be integers of different bases (e.g. `0x28`, `40` or `0b101000`) or arithmetic expressions, that are later evaluated (e.g. `(AXI_DATA_WIDTH+1)/4` is a valid parameter value assuming that a parameter named `AXI_DATA_WIDTH` exists in the same IP core). You can also write a parameter value in a Verilog format (e.g. `8'b00011111` or `8'h1F`) - in such cases, it will be interpreted as a fixed-width bit vector.

* Connecting IP cores' ports and interfaces. Only connections between ports or interfaces of matching types are allowed. This is automatically checked by the GUI, as the types of nodes' ports and interfaces are contained in the loaded specification, so the GUI will prevent you from connecting non-matching interfaces (e.g. *AXI4* with *AXI4Lite* or a port with an interface). A green line will be displayed if a connection is possible to create, or a red line elsewhere:
```{image} img/invalid_connection.png
```

* Specifying external ports or interfaces in the top module. This can be done by adding `External Input`, `External Output` or `External Inout` metanodes and creating connections between them and the chosen ports or interfaces. Note that you should adjust the name of the external port or interface in the textbox inside the selected metanode. In the example below, the output port `pwm` of `litex_pwm_top` IP core is external to the generated top module and the external port name will be set to `ext_pwm`:
```{image} img/external_port.png
```

An example block design in Pipeline Manager for the PWM project may look like this:
```{kpm_iframe}
:spec: ../build/kpm_jsons/spec_pwm.json
:dataflow: ../build/kpm_jsons/data_pwm.json
```

More information about this example can be found [here](https://antmicro.github.io/topwrap/examples.html#pwm)

## CLI

Topwrap has a couple of CLI only functions that expand on the functionality offered by the GUI.

(generating-ip-yamls)=
### Generating IP core description YAMLs

You can use Topwrap to generate IP core description YAMLs from HDL sources to use in your `project.yml`.
To learn more about project and core YAMLs, check the {ref}`design description <design-description>` and {ref}`ip description <ip-description>`

```
python -m topwrap parse HDL_FILES
```

In HDL source files, ports that belong to the same interface (e.g. wishbone or AXI),
often have a common prefix, which corresponds to the interface name. If the naming
convention is followed in the HDL sources, Topwrap can also divide ports into user-specified
interfaces, or automatically deduce interface names when generating YAML files:

```
python -m topwrap parse --iface wishbone --iface s_axi HDL_FILES

python -m topwrap parse --iface-deduce HDL_FILES
```

For help, use:

```
python -m topwrap [build|kpm_client|parse] --help
```

## Validating designs

Pipeline Manager can perform basic runtime checks, including interface type verification when creating a connection. More complex tests can be run by using Pipeline Manager's `Validate` option. Topwrap will then respond with a validity confirmation or an error message. There is [dedicated chapter](link to checks.md) explaining the validation done by Topwrap.
