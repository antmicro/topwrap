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
    clocks:
      {module_clock_name}: {domain_name}
    resets:
      {module_reset_name}: {domain_name}
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

clock_domains:
  default:
    signal: [{ip_name}, {port_name}]
  {other_domain_name}:
    signal: [{ip_name}, {port_name}]
  {another_domain_name}:
    signal: {external_port_name}
  ...

reset_domains:
  default:
    signal: [{ip_name}, {port_name}]
    polarity: active high
  {other_domain_name}:
    signal: [{ip_name}, {port_name}]
    polarity: active low
  {another_domain_name}:
    signal: {external_port_name}
    polarity: active low
    synchronous_to: default
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

memory_maps:
  {memory_map_name}: # this name is referenced in an interconnect
    {instance_name}: # component instance reference
      {interface_name1}: # interface of component
        address: {address1}
        {additional_parameter_name}: {value_accepted_by_an_interconnect_implementation} # additional parameters for specific interconnects can be specified
        ...
      {interface_name2}:
        address: {address2}
        size: {size2} # a default size can be overwritten
    ...
    {instance_name}: # when an instance has only one interface, it is not required to specify the interface name
      address: {address1}
```

`inout` ports are handled differently than the `in` and `out` ports. When an IP has an inout port or when a hierarchy has an inout port specified in its `external.ports.inout` section, it must be included in the `external.ports.inout` section of the parent design. It is required to specify the name of the IP/hierarchy and the port name that contains it. The name of the external port is identical to the one in the IP core. In case of duplicate names, a suffix `$n` is added (where `n` is a natural number) to the name of the second and subsequent duplicate names. `inout` ports cannot be connected to each other.

The design description YAML format allows for creating hierarchical designs. In order to create a hierarchy, add its name as a key in the `hierarchies` section and describe the hierarchy design "recursively" by using the same keys and values (`ports`, `parameters` etc.) as in the top-level design (see above). Hierarchies can be nested recursively, which means that you can create a hierarchy inside another one.

Note that IPs and hierarchies names cannot be duplicated on the same hierarchy level, as each entry in `hierarchies` is treated as equal with entries in `ips`.

Additionally, designs can contain clock and reset domains.
These domains allow for automatic wiring of clock and reset inputs of IP cores, and performing sanity checks for interface connections.
Domains reference a port that acts as the source. This may be either a module port (for example from a PLL instance), or an external port.

Additionally, reset domains contain information about the reset signal's polarity and whether it's synchronous to some domain or asynchronous.
The polarity may be either `active low` or `active high`.
The synchronicity is specified via the `synchronous_to` key, which can be `null`/omitted if asynchronous, or otherwise specifies the name of a clock domain.

When instantiating IP cores, their clocks and resets can be assigned to domains via the `clocks` and `resets` keys.
If a domain is not assigned explicitly, the clock/reset signal is implicitly assigned to the corresponding `default` domain.

For reset connections, Topwrap will automatically invert connections between resets of different polarities.
For resets that don't have the same synchronicity, an error is raised describing the problem.

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

The primary purpose of the IP core YAML is to provide the tool with essential metadata and structural information about a specific IP core to facilitate automated SoC assembly.
It contains information about signals, clock domains, parameterization and interfaces.
Interfaces are defined as a list of signals and parameters such as `mode` and `type`.

The example below presents an example IP YAML core description file.

```yaml
id:
  library: libdefault
  name: axi4_to_ahb
  vendor: vendor

parameters:
  RESET_ADDRESS: 32'h80000000

signals:
  in:
    - sys_clk
    - sys_rst
    - name: core_id
      bound: [3, 0]
      default: 0
    - name: wb_req
      type: wb_req_t
  out:
    - core_halted
    - name: wb_resp
      type: wb_resp_t

interfaces:
  ifu_axi:
    type:
      name: AXI4
      vendor: vendor
      library: libdefault
    mode: manager
    # the size field in manager mode is unused by topwrap
    signals:
      out:
        bready: ifu_bready
        awaddr: [ifu_awaddr, 31, 0]
        # ... remainder of AXI signals ...
      in:
        awready: ifu_awready
        rdata: [ifu_rdata, 63, 0]
        # ... remainder of AXI signals ...
  iface1_wb:
    type: wishbone
    mode: subordinate
    size: 0xFFFF # the size field in subordinate mode is optional
    signals:
      # wishbone signals
      addr:
        path: wb_req.addr

types:
  wb_req_t:
    members:
      - name: cyc
        type: [0, 0]
      - name: addr
        type: ...
      ...
  wb_resp_t:
    members:
      ...
```

### File format explanation

- `id` \- identification of the Core. An instance of [Identifier IR class](developers_guide/internal_representation.html#topwrap.model.misc.Identifier)
  - `library` \- by default `libdefault`
  - `vendor` \- by default `vendor`
  - `name` \- same as the name in the HDL file
- `parameters` \- a dictionary with IP core parameters
- `signals` \- contains the names of signals used in the module ports
  - `out` \- a list of signals that are in the output direction
  - `in` \- a list of signals that are in the input direction
  - `inout` \- a list of signals that can be both input and output, similar to an `inout` port in Verilog
- `interfaces` \- a list of interfaces
  - `type` \- the [ID](developers_guide/internal_representation.html#topwrap.model.misc.Identifier) of the interface definition that is used for that interface. See the [Interface Definition YAML](#interface-description-files).
  - `mode` \- `manager`, `subordinate` or `unspecified`. When generating ports, the mode is used to determine the direction of the port. `unspecified` behaves the same as `manager`. When doing inference, all newly created interfaces have their `type` set to `unspecified`.
  - `size` \- the optional field that is only used when `mode` is `subordinate`, it is used when there is an instance of this module specified in `address_maps` in the design YAML.
  - `signals` \- a list of signals mapped to ports. Signals from the interface definition need to be mapped to ports in the HDL module.
- `types` \- structure type definitions used by signals (described below in more detail)
  - `members` \- member fields of a struct type

### Signals

Each signal (for both port and interface definitions) can be specified in one of two formats.

#### New signal format

The signal is defined by a YAML object, with the following properties:

 - `name` (optional) - the name of the signal.
 - `bound` (optional) - the bounds of the bit range, determining the width.
 - `slice` (optional) - the bounds of the slice bit range (only applicable to interface definitions).
 - `default` (optional) - default value to assign to this port if nothing is connected to it, applicable only to input ports.
 - `type` (optional) - the name of the type (defined in the `types` section) used for this signal
 - `path` (optional) - the path to a field to use as the source for this signal

A signal must have either a `name` or a `path` specified, but not both at once.

Additionally, `path` may only be specified for interface signals.
For example, a path of `some_port.some_field` describes a signal that uses a subfield of a port.
Paths can also describe slices, e.g. `some_port[31:0]` is equivalent to specifying a `name` of `some_port` and a `slice` of `[31, 0]`.
Paths can use any combination of slicing and field selection operations, e.g. `some_port[3].some_field[1].some_other_field[31:0]`.

A signal may specify `bound` or `type` (or neither for a single bit port), but not both at the same time.

Example port definitions using this format:

```yaml
signals:
    in:
        - name: foo
          bound: [31, 0]
          default: 32'hDEADBEEF
        - name: bar
          type: some_struct_t
```

Example interface signal definitions using this format:

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
                QUX:
                    path: some_struct_port.qux
```

#### Old signal format

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

#### Types

IP core YAML files may additionally describe types used by the module's ports in a dedicated section.
This is primarily intended to support modules using structure ports.

Each named type is defined in the `types` section:

```yaml

types:
  my_struct_type_t:
    ...
  my_other_type_t:
    ...
```

Each type is either:

 - a two element array describing a bit vector (incl. single bits), e.g. `[31, 0]` or `[0, 0]`
 - an object with a `members` describing a struct, described below

The members of a struct are defined in an array of field objects, each of which consists of the following properties:

 - `name` - the name of the field
 - `type` - the type definition for the field

Example struct definition describing AXI output signals:

```yaml

types:
  my_axi_req_t:
    members:
      - name: aw_valid
        type: [0, 0]
      - name: aw
        type:
          members:
            - name: addr
              type: [31, 0]
            ...
      ...
```

### Interface definitions

The purpose of the interface YAML file is to store information about interface definitions. These definitions are used for inferring ports to interface instances. It contains the id of the interface, which is used to reference the definition from the IP core YAML file.
The YAML file separates `signals` into those that are required for a list of ports to be interpreted as this interface and optional signals that, if present, are inferred into a single interface instance.

Regular expressions are used to find ports in the HDL module that correspond to the signals in the interface definition.

```yaml
id:
  library: libdefault
  name: wishbone
  vendor: vendor
signals:
    required:
        out:
            cyc: cyc
            stb: stb
        in:
            ack: ack
    optional:
        out:
            dat_w: dat_(w|mosi)|mosi
            adr: adr
            tgd_w: tgd_w
            lock: lock
            sel: sel
            tga: tga
            tgc: tgc
            we: we
            cti: cti
            bte: bte
        in:
            dat_r: dat_(r|miso)|miso
            tgd_r: tgd_r
            stall: stall
            err: err
            rty: rty
```
File format explanation:

- `id` \- identification of the interface. An instance of [Identifier IR class](developers_guide/internal_representation.html#topwrap.model.misc.Identifier)
  - `library` \- by default `libdefault`
  - `vendor` \- by default `vendor`
  - `name` \- same as the name in the HDL file
- `signals` \- contains the names of signals with regular expressions that are used in the ports of Modules.
  - `required` \- contains signals that must be present in the list of ports in the module
  - `optional` \- contains signals that are connected to the interface instance when present in the list of ports in the module
    - `out` \- a list of signals that are in the output direction
    - `in` \- a list of signals that are in the input direction
    - `inout` \- a list of signals that can be both the input and the output, similar to an `inout` port in Verilog

Interfaces can also specify which clock and reset input of the IP core they use.
This is done via the optional `clock` and `reset` keys, which specify the name of the input (see below).

When connecting interfaces that have clock inputs assigned on both sides of the connection, Topwrap will automatically perform sanity checks, and report errors for connections between interfaces that belong to different clock domains.

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

### Clock and reset inputs

IPs can define clock and reset inputs, which allow for automatic connections to clock/reset domains within a design.
Each clock/reset specifies a port that is used for it.
Additionally, reset inputs specify polarity and synchronicity similarly to reset domains in the design description.

Example clock and reset definition:

```yaml
# Two independent clocks
clocks:
  some_clock:
    signal: some_clock_port
  some_other_clock:
    signal: some_other_clock_port

# Two resets, one synchronous, one asynchronous
resets:
  some_reset:
    signal: some_reset_port
    polarity: active high
    synchronous_to: some_other_clock
  some_other_reset:
    signal: some_other_reset_port
    polarity: active low
    synchronous_to: null
```

In both cases, the `signal` key defines which of the module's ports belongs to this clock/reset.
The `polarity` and `synchronous_to` keys are the same as the ones in the design description, with one difference: in IP cores `synchronous_to` references a clock input, not a clock domain.

## Interface definition files

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
- `git`
  - `SCHEME_ARGS`:
    1. An optional git ref (branch, tag, or commit SHA) to check out. If omitted, the repository's default branch is used.
    2. An optional subdirectory inside the repository to use as the resolved path.
  - `SCHEME_PATH`: The URL of a git repository to clone.


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

```
git[main]:https://github.com/antmicro/topwrap.git
```

This clones the `main` branch of the given git repository into a persistent cache directory and uses it as the resource location. Omitting the `[main]` argument checks out the repository's default branch instead. A commit SHA can be used in place of a branch or tag name.

```
git[main|topwrap/builtin]:https://github.com/antmicro/topwrap.git
```

This clones the `main` branch as above, but resolves to the `main|topwrap/builtin` subdirectory of the repository instead of its root.

Cloned repositories are cached persistently between runs. To remove all locally cached clones, run:

```
topwrap clean-cache --target git
```

Omitting `--target` removes every cache topwrap maintains.
