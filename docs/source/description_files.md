(description-files)=
# Creating a design

This chapter describes how to create a design in Topwrap, including a detailed overview of Topwrap design files are structured.

(design-description)=
## Design description

To create a complete and fully synthesizable design, a design file is needed. It is used for:

* specifying interconnects and IP cores
* setting parameter values and describing hierarchies for the project
* connecting the IPs and hierarchies
* picking external ports (those which will be connected to the physical I/O).

You can see example design files in the `examples` directory. The structure of the design file is below:

```yaml
ips:
  # specify relations between IP instance names in the
  # design yaml and IP cores description YAMLs
  {ip_instance_name}:
    file: {path_to_ip_description}
  ...

design:
  name: {design_name} # optional name of the toplevel
  hierarchies:
      # see "Hierarchies" below for a detailed description of the format
      ...
  parameters: # specify IP parameter values to be overridden
    {ip_instance_name}:
      {parameters_name} : {parameters_value}
      ...
  ports:
    # specify the incoming ports connections of an IP named `ip1_name`
    {ip1_name}:
      {port1_name} : [{ip2_name}, {port2_name}]
      ...
    # specify the incoming ports connections of a hierarchy named `hier_name`
    {hier_name}:
      {port1_name} : [{ip_name}, {port2_name}]
      ...
    # specify the external port connections
    {ip_instance_name}:
      {port_name} : ext_port_name
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
```

`inout` ports are handled differently than the `in` and `out` ports. When an IP has an inout port or when a hierarchy has an inout port specified in its `external.ports.inout` section, it must be included in the `external.ports.inout` section of the parent design. It is required to specify the name of the IP/hierarchy and the port name that contains it. The name of the external port is identical to the one in the IP core. In case of duplicate names, a suffix `$n` is added (where `n` is a natural number) to the name of the second and subsequent duplicate names. `inout` ports cannot be connected to each other.

The design description YAML format allows for creating hierarchical designs. In order to create a hierarchy, add its name as a key in the `design` section and describe the hierarchy design "recursively" by using the same keys and values (`ports`, `parameters` etc.) as in the top-level design (see above). Hierarchies can be nested recursively, which means that you can create a hierarchy inside another one.

Note that IPs and hierarchies names cannot be duplicated on the same hierarchy level. For example, the `design` section cannot contain two identical keys, but it is possible to have `ip_name` key in this section and `ip_name` in the `design` section of a separate hierarchy.

(design-description-hierarchies)=
### Hierarchies

Hierarchies allow for creating designs with subgraphs in them. The subgraphs can contain multiple IP cores and other subgraphs, allowing for the creation of nested designs in Topwrap.

(design-description-format)=
### Format

Hierarchies are specified in the design description.
The `hierarchies` key must be a direct descendant of the `design` key.
The format is as follows:

```yaml
hierarchies:
    {hierarchy_name_1}:
      ips: # ips that are used on this hierarchy level
        {ip_name}:
          ...

      design:
        parameters:
          ...
        ports: # ports connections internal to this hierarchy.
          # note that also you have to connect port to it's external port equivalent (if exists).
          {ip1_name}:
              {port1_name} : [{ip2_name}, {port2_name}]
              {port2_name} : {port2_external_equivalent} # connection to external port equivalent. Note that it has to be the parent port.
            ...
        hierarchies:
          {nested_hierarchy_name}:
            # structure here will be the same as for {hierarchy_name_1}
            ...
      external:
        # external ports and/or interfaces of this hierarchy; these can be
        # referenced in the upper-level `ports`, `interfaces` or `external` section
        ports:
            in:
              - {port2_external_equivalent}
        ...
    {hierarchy_name_2}:
      ...
```

A more complex example of a hierarchy can be found in the [examples/hierarchy](https://github.com/antmicro/topwrap/tree/main/examples/hierarchy) directory.

(design-description-ip-description)=
## IP description files

Every IP wrapped by Topwrap needs a description file in the YAML format.

The ports of an IP should be placed in the global `signals` key, followed by the direction - `in`, `out` or `inout`.
The module name of an IP should be placed in the global `name` key, and it should be consistent with the definition in the HDL file.
As an example, this is the description of ports in the Clock Crossing IP:

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

The previous example can be used with any IP. However, in order to benefit from connecting entire interfaces simultaneously, the ports must belong to a named interface like in this example:

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
Each signal in an interface has a name which must match with the signal that it is connected to, for example `TDATA: port_name` connects to `TDATA: other_port_name`.

To speed up the generation of YAMLs, Topwrap's `parse` command (see {ref}`Generating IP core description YAMLs <advanced-options-CLI-generating-ip-yamls>`) can be used to generate YAMLs from HDL source files.

(design-description-port-widths)=
### Port widths
You can specify the port width in the following format:

```yaml
signals:
    in:
        - [port_name, upper_limit, lower_limit]
```
* `port_name` - name of the port.
* `upper_limit` and `lower_limit` define the bit range, where `[upper_limit, lower_limit]` determines the number of bits for the port (e.g. `[63, 0]` for **64 bits**).

As an example:
```yaml
signals:
    in:
        - [gpio_io_i, 31, 0] # 32 bits
```

If the bit range is omitted:
```yaml
signals:
    in:
      - port_name
```
then the default width of `port_name` is **1 bit**.

You can also specify the signal width within interfaces.
```yaml
interfaces:
    s_axis:
        type: AXIStream
        mode: subordinate
        signals:
            in:
                TDATA: [s_axis_tdata, 63, 0] # 64 bits
                ...
                TVALID: s_axis_tvalid # defaults to 1 bit
```
* **TDATA** is assigned to `s_axis_tdata` and is 64 bits wide, defined by `[63, 0]`.
* **TVALID** is assigned to `s_axis_tvalid` and, without a specified range, defaults to **1 bit**.

(design-description-parameterization)=
### Parameterization

Port widths don't have to be hardcoded, as parameters can describe an IP core in a generic way, and values specified in IP core YAMLs can be overridden in a design description file (see {ref}`Design Description <design-description>`).
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

The parameter values can be integers or math expressions, which are evaluated using `simpleeval`.

(design-description-port-slicing)=
### Port slicing

Ports can be sliced for using some parts of the port as a signal that belongs to a defined interface.

As an example:
`Port m_axi_bid of the IP core is 36 bits wide. Use bits 23..12 as the BID signal of the AXI manager is named m_axi_1`

```yaml
m_axi_1:
    type: AXI
    mode: manager
    signals:
        in:
            BID: [m_axi_bid, 35, 0, 23, 12]
```

(design-description-interface-description-files)=
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
Note that clock and reset are not included as these are usually inputs to both the manager and subordinate, so they are not supported in the interface specification.
Every signal is a key-value pair, where the key is a generic signal name (normally taken from the interface specification) and used to identify it in other parts of Topwrap (i.e. IP core description files), and the value is a regex used to deduce which port defined in the HDL sources represents this signal.

### Interface deduction

During [IP core parsing](#advanced-options-CLI-generating-ip-yamls), you can use the `--iface-deduce` flag to enable automatic pairing of raw ports from HDL sources to interface signals.

This feature matches signal regexes from all available interface descriptions with raw port names of the IP Core in order to discover possible interface instances.
The pairing is performed on port names that are transformed to lowercase and have the common `port_prefix` removed, which means that the regexes must also be written in lowercase.

### Interface compliance

During the [build process](#getting-started-command-line-flow-generating-verilog-top-files), an optional verification of whether the interface instances used in IP cores are compliant with their respective descriptions can be enabled.
The verification consists of checking in the instance if:
- all signals designated as required in the description are included.
- no additional signals beyond those defined in the description are included.

This feature is controlled by the `--iface-compliance` CLI flag or the `force_interface_compliance` key in the [configuration file](user_repositories.md) <!-- we don't really have a proper section about the configuration yet --> and is turned off by default.