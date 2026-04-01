# Creating a design

This chapter explains how to create a design in Topwrap, including a detailed overview of how Topwrap design files are structured.

## Design description

To create a complete and fully synthesizable design, a design file is needed. It is used for:

* specifying IP cores and their parameters
* specifying interconnects
* describing hierarchies for the project
* connecting the IPs and hierarchies
* defining design interfaces and ports

You can see example design files in the `examples` directory. The structure of the design file is shown below:

```yaml
name: {design_name} # optional name of the toplevel

ips:
  # specify relations between IPs instance names in the
  # design yaml and IP cores description YAMLs
  {ip1_instance_name}:
    file: {resource_path} # see "Resource path syntax" section for more information
    parameters:  # specify IP parameter values to be overridden
      {parameters_name} : {parameters_value}
      ...
  ...

connections:
  ports:
    # specify the incoming ports connections of an IP named `ip1_name`
    {ip1_name}:
      {port1_name} : [{ip2_name}, {port2_name}]
      # connections between modules can be (bit-wise) inverted
      {port3_name} : ~[{ip2_name}, {port4_name}]
      ...
    # specify the incoming ports connections of a hierarchy named `hier_name`
    {hier_name}:
      {port1_name} : [{ip_name}, {port2_name}]
      ...
    # specify the external port connections
    {ip_instance_name}:
      {port_name} : ext_port_name
      # connections to external ports can be (bit-wise) inverted
      {other_port_name} : ~other_ext_port_name
    ...

  interfaces:
    # specify the incoming interface connections of the `ip1_name` IP
    {ip1_name}:
      {interface1_name} : [{ip2_name}, {interface2_name}]
      ...
    # specify the incoming interface connections of the `hier_name` hierarchy
    {hier_name}:
      {interface1_name} : [{ip_name}, {interface2_name}]
      ...
    # specify the external interface connections
    {ip_instance_name}:
      {interface_name} : ext_interface_name
    ...

interconnects:
  # see the "Interconnect generation" page for a detailed description of the format
  ...
external: # specify the names of external ports and interfaces of the top module
ports:
  out:
    - {ext_port_name}
  inout:
    - [{ip_name/hierarchy_name, port_name}]
interfaces:
  in:
    - {ext_interface_name}
  # note that `inout:` is invalid in the interfaces section

hierarchies:
   # see "Hierarchies" below for a detailed description of the format
      ...
```

`inout` ports are handled differently than the `in` and `out` ports. When an IP has an inout port or when a hierarchy has an inout port specified in its `external.ports.inout` section, it must be included in the `external.ports.inout` section of the parent design. It is required to specify the name of the IP/hierarchy and the port name that contains it. The name of the external port is identical to the one in the IP core. In case of duplicate names, a suffix `$n` is added (where `n` is a natural number) to the name of the second and subsequent duplicate names. `inout` ports cannot be connected to each other.

The design description YAML format allows for creating hierarchical designs. In order to create a hierarchy, add its name as a key in the `design` section and describe the hierarchy design "recursively" by using the same keys and values (`ports`, `parameters` etc.) as in the top-level design (see above). Hierarchies can be nested recursively, which means that you can create a hierarchy inside another one.

Note that IPs and hierarchies names cannot be duplicated on the same hierarchy level. For example, the `design` section cannot contain two identical keys, but it is possible to have `ip_name` key in this section and `ip_name` in the `design` section of a separate hierarchy.

### Hierarchies

Hierarchies allow for creating designs with subgraphs in them. The subgraphs can contain multiple IP cores and other subgraphs, allowing for the creation of nested designs in Topwrap.

### Format

Hierarchies are specified in the [design description](#design-description). The `hierarchies` key must be a direct descendant of the `design` key.

The format is as follows:

```yaml
hierarchies:
  {hierarchy_name_1}:
     # Design description, see above
     ...
```

A more complex example of a hierarchy can be found in the [examples/hierarchy](https://github.com/antmicro/topwrap/tree/main/examples/hierarchy) directory.

## IP description files

IP description files are used to provide definitions for modules external to the topwrap design. Each file contains the specification of the module's name, its ports, and its interfaces.
The module name of an IP should be placed in the global `name` key, and it should be consistent with the definition in the HDL file.
The ports of an IP should be placed in the global `signals` key, followed by the direction - `in`, `out` or `inout`.

Each signal (for both port and interface definitions) can be specified in one of two formats.

### New signal format

The signal is defined by a YAML object, with the following properties:

 - `name` (required) - the name of the signal.
 - `bound` (optional) - the bounds of the bit range, determining the width.
 - `slice` (optional) - the bounds of the slice bit range (only applicable to interface definitions).
 - `default` (optional) - default value to assign to this port if nothing is connected to it, applicable only to input ports.

Example port definition using this format:

```yaml
signals:
    in:
        - name: foo
          bound: [31, 0]
          default: 32'hDEADBEEF
```

Example interface signal definition using this format:

```yaml
interfaces:
    foo:
        type: AXIStream
        mode: subordinate
        signals:
            in:
                BAR:
                    name: bar
                    bound: [63, 0]
                    slice: [47, 16]
                ...
                BAZ:
                    name: BAZ
```

### Old signal format

The signal is defined by either:

 - just a name (implied one-bit signal):

   ```yaml
   signals:
       in:
           - foo
   ```

 - an array consisting of the name and the bounds of the bit range:

   ```yaml
   signals:
       in:
           - [foo, 31, 0]
   ```

 - an array consisting of the name, the bounds of the bit range, and the bounds of the slice bit range (only applicable to interface definitions):

   ```yaml
   signals:
       in:
           TDATA: [foo, 63, 0, 47, 16]
   ```

As an example, this is the description of ports in the `Clock Crossing` IP:

```yaml
# file: clock_crossing.yaml
name: cdc_flag
signals:
    in:
        - clkA
        - A
        - clkB
    out:
        - B
```

### Interface definitions

The previous example can be used with any IP. However, in order to benefit from connecting entire interfaces simultaneously, the ports must belong to a named interface as in this example:

```yaml
#file: axis_width_converter.yaml
name: axis_width_converter
interfaces:
    s_axis:
        type: AXIStream
        mode: subordinate
        signals:
            in:
                TDATA: [s_axis_tdata, 63, 0]
                TKEEP: [s_axis_tkeep, 7, 0]
                TVALID: s_axis_tvalid
                TLAST: s_axis_tlast
                TID: [s_axis_tid, 7, 0]
                TDEST: [s_axis_tdest, 7, 0]
                TUSER: s_axis_tuser
            out:
                TREADY: s_axis_tready
    m_axis:
        type: AXIStream
        mode: manager
        signals:
            in:
                TREADY: m_axis_tready
            out:
                TDATA: [m_axis_tdata, 31, 0]
                TKEEP: [m_axis_tkeep, 3, 0]
                TVALID: m_axis_tvalid
                TLAST: m_axis_tlast
                TID: [m_axis_tid, 7, 0]
                TDEST: [m_axis_tdest, 7, 0]
                TUSER: m_axis_tuser
signals: # These ports do not belong to an interface
    in:
        - clk
        - rst
```

The names `s_axis` and `m_axis` will be used to group the selected ports.
Each signal in an interface has a name which must match with the signal that it is connected to, for example `TDATA: port_name` must connect to `TDATA: other_port_name`.

### Parameterization

Port widths don't have to be hardcoded, as parameters can describe an IP core in a generic way, and values specified in IP core YAMLs can be overridden in a design description file (see [Design description](description_files.md#design-description)).

```yaml
parameters:
    DATA_WIDTH: 8
    KEEP_WIDTH: (DATA_WIDTH+7)/8
    ID_WIDTH: 8
    DEST_WIDTH: 8
    USER_WIDTH: 1

interfaces:
    s_axis:
        type: AXI4Stream
        mode: subordinate
        signals:
            in:
                TDATA: [s_axis_tdata, DATA_WIDTH-1, 0]
                TKEEP: [s_axis_tkeep, KEEP_WIDTH-1, 0]
                ...
                TID: [s_axis_tid, ID_WIDTH-1, 0]
                TDEST: [s_axis_tdest, DEST_WIDTH-1, 0]
                TUSER: [s_axis_tuser, USER_WIDTH-1, 0]
```

The parameter values can be integers or math expressions.

## Interface description files

Topwrap can use predefined interfaces, as illustrated in YAML files that come packaged with the tool.
The currently supported interfaces are AXI3, AXI4, AXI Lite, AXI Stream and Wishbone.

An example file looks as follows:

```yaml
name: AXI4Stream
port_prefix: AXIS
signals:
    # The convention assumes the AXI Stream transmitter (manager) perspective
    required:
        out:
            TVALID: tvalid
            TDATA: tdata
            TLAST: tlast
        in:
            TREADY: tready
    optional:
        out:
            TID: tid
            TDEST: tdest
            TKEEP: tkeep
            TSTRB: tstrb
            TUSER: tuser
            TWAKEUP: twakeup
```

The `name` of an interface must be unique.

Signals are either required or optional, and their direction is described from the perspective of the manager (i.e. the direction of signals in the subordinate are flipped).
Note that `clock` and `reset` are not included as these are usually inputs to both the manager and subordinate, so they are not supported in the interface specification.
Every signal is a key-value pair, where the key is a generic signal name (normally taken from the interface specification) and used to identify it in other parts of Topwrap (i.e. IP core description files), and the value is a regex used to deduce which port defined in the HDL sources represents this signal.

### Interface compliance

During the [build process](getting_started.md#building-designs-with-topwrap), an optional verification of whether the interface instances used in IP cores are compliant with their respective descriptions can be enabled. The verification consists of checking in the instance if:

- all signals designated as required in the description are included.
- no additional signals beyond those defined in the description are included.

This feature is controlled by the `--iface-compliance` CLI flag or the `force_interface_compliance` key in the [configuration file](config.md#available-config-options) and is turned off by default.


## Resource path syntax

Fields specified in the YAML file as a "resource path" support extended functionality and have their own specific syntax.

This field type is used for example in the [Design Description](#design-description) for specifying an IP Core description location:

```yaml
ips:
  ip_inst_name:
    file: {resource path}
...
```

The syntax is as follows:

```
SCHEME[ARG1|ARG2...]:SCHEME_PATH
```

- `SCHEME` is the scheme of this path (e.g. `get` for remote resources)
- `ARGS` are `|`-separated positional arguments for the specific scheme (e.g. the user repo name for the `repo` scheme)
  - If there are no arguments to supply you can omit the square brackets entirely
- `SCHEME_PATH` is the path to the resource interpreted by the specific scheme (e.g. the URL for the `get` scheme)

### Available schemes

- `file`
  - `SCHEME_ARGS`: None
  - `SCHEME_PATH`: A filesystem path relative from the currently edited YAML file to the resource
- `repo`
  - `SCHEME_ARGS`: Repository name
  - `SCHEME_PATH`: A name of resource
- `get`
  - `SCHEME_ARGS`: None
  - `SCHEME_PATH`: The URL address of the remote resource. Only `http(s)://` URLs are currently supported.


:::{warning}
If a repository was injected to the config with the `--repo` CLI option, the name of such repository will be the name of the directory containing it.
:::

### Examples


```
file:./my_directory/file.txt
```

A path to the file on the filesystem.

```
repo[builtin]:axi_protocol_converter
```

This loads the `axi_protocol_converter` core located in the builtin user repository.

```
repo[my_repo]:res.txt
```

This loads the `res.txt` file inside the `my_repo` loaded user repository.

```
get:https://raw.githubusercontent.com/antmicro/topwrap/refs/heads/main/pyproject.toml
```

This loads the remote resource.
When necessary, it's automatically downloaded into a temporary directory.
