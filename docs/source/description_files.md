(description-files)=

# Description files

(design-description)=

## Design Description

To create a complete, fully synthesizable design, a proper design file is needed.
It's used to specify interconnects, IP cores, set their parameters' values, describe hierarchies for the project,
connect the IPs and hierarchies, and pick external ports (those which will be connected to physical I/O).

You can see example design files in `examples` directory. The structure is as below:

```yaml
ips:
  # specify relations between IPs names in the design yaml
  # and IP cores description yamls and modules
  {ip_instance_name}:
    file: {path_to_yaml_file_of_the_ip}
    module: {name_of_the_HDL_module}
  ...

design:
  name: {design_name} # optional name of the toplevel
  hierarchies: # specify hierarchies designs
    {hierarchy_name_1}:
      design:
        parameters:
          ...
        ports: # ports connections internal to this hierarchy
          ...
        interfaces: # interfaces connections internal to this hierarchy
          ...
        {nested_hierarchy_name}:
          ...
      external:
        # external ports and/or interfaces of this hierarchy; these can be
        # referenced in the upper-level `ports`, `interfaces` or `external` section
        ...
    {hierarchy_name_2}:
      ...

  parameters: # specify IPs parameter values to be overridden
    {ip_instance_name}:
      {param_name} : {param_value}
      ...

  ports:
    # specify incoming ports connections of an IP named `ip1_name`
    {ip1_name}:
      {port1_name} : [{ip2_name}, {port2_name}]
      ...
    # specify incoming ports connections of a hierarchy named `hier_name`
    {hier_name}:
      {port1_name} : [{ip_name}, {port2_name}]
      ...
    # specify external ports connections
    {ip_instance_name}:
      {port_name} : ext_port_name
    ...

  interfaces:
    # specify incoming interfaces connections of `ip1_name` IP
    {ip1_name}:
      {iface1_name} : [{ip2_name}, {iface2_name}]
      ...
    # specify incoming interfaces connections of `hier_name` hierarchy
    {hier_name}:
      {iface1_name} : [{ip_name}, {iface2_name}]
      ...
    # specify external interfaces connections
    {ip_instance_name}:
      {iface_name} : ext_iface_name
    ...

  interconnects:
    # see "Interconnect generation" page for a detailed description of the format
    ...

external: # specify names of external ports and interfaces of the top module
  ports:
    out:
      - {ext_port_name}
    inout:
      - [{ip_name/hierarchy_name, port_name}]
  interfaces:
    in:
      - {ext_iface_name}
```

In order for an IP to be present in the generated design, it must be specified in `ports` or `interfaces` sections as a key. This means that even if it has no incoming connections from any other IP or hierarchy, the `ports` or `interfaces` sections must contain `ip_name: {}` entry.

`inout` ports are handled differently than `in` and `out` ports. When any IP has an inout port or when a hierarchy has an inout port specified in its `external.ports.inout` section, it must be included in `external.ports.inout` section of the parent design by specifying the name of the IP/hierarchy and port name that contains it. Name of the external port will be identical to the one in the IP core. In case of duplicate names a suffix `$n` is added (where `n` is a natural number) to the name of the second and subsequent duplicate names. `inout` ports cannot be connected to each other.

The design description yaml format allows creating hierarchical designs. In order to create a hierarchy, it suffices to add its name as a key in the `design` section and describe the hierarchy design "recursively" by using the same keys and values (`ports`, `parameters` etc.) as in the top-level design (see above). Hierarchies can be nested recursively, which means that you can create a hierarchy inside another one.

Note that IPs and hierarchies names cannot be duplicated on the same hierarchy level. For example, the `design` section cannot contain two identical keys, but it's correct to have `ip_name` key in this section and `ip_name` in the `design` section of some hierarchy.

(ip-description)=

## IP description files

Every IP wrapped by Topwrap needs a description file in YAML format.

The ports of an IP should be placed in global `signals` node, followed by the direction of `in`, `out` or `inout`.
Here's an example description of ports of Clock Crossing IP:

```yaml
# file: clock_crossing.yaml
signals:
    in:
        - clkA
        - A
        - clkB
    out:
        - B
```

The previous example is enough to make use of any IP. However, in order to benefit from connecting whole interfaces at once, ports must belong to a named interface like in this example:

```yaml
#file: axis_width_converter.yaml
s_axis:
    interface: AXIStream
    mode: slave
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
    interface: AXIStream
    mode: master
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
signals: # These ports don't belong to any interface
    in:
        - clk
        - rst
```

Names `s_axis` and `m_axis` will be used to group the selected ports.
Each signal in an interface has a name which must match with the signal it's supposed to be connected to, for example `TDATA: port_name` will be connected to `TDATA: other_port_name`.

Note that you don't have to write IP core description yamls by hand. You can use Topwrap's `parse` command (see {ref}`Generating IP core description YAMLs <generating-ip-yamls>`) in order to generate yamls from HDL source files and then adjust the yaml to your needs.

### Port widths

The width of every port defaults to `1`.
You can specify the width using this notation:

```yaml
s_axis:
    interface: AXIStream
    mode: slave
    signals:
        in:
            TDATA: [s_axis_tdata, 63, 0] # 64 bits
            ...
            TVALID: s_axis_tvalid # defaults to 1 bit

signals:
    in:
        - [gpio_io_i, 31, 0] # 32 bits
```

### Parameterization

Port widths don't have to be hardcoded - you can use parameters to describe an IP core in a generic way.
Values specified in IP core yamls can be overridden in a design description file (see {ref}`Design Description <design-description>`).

```yaml
parameters:
    DATA_WIDTH: 8
    KEEP_WIDTH: (DATA_WIDTH+7)/8
    ID_WIDTH: 8
    DEST_WIDTH: 8
    USER_WIDTH: 1

s_axis:
    interface: AXI4Stream
    mode: slave
    signals:
        in:
            TDATA: [s_axis_tdata, DATA_WIDTH-1, 0]
            TKEEP: [s_axis_tkeep, KEEP_WIDTH-1, 0]
            ...
            TID: [s_axis_tid, ID_WIDTH-1, 0]
            TDEST: [s_axis_tdest, DEST_WIDTH-1, 0]
            TUSER: [s_axis_tuser, USER_WIDTH-1, 0]
```

Parameters values can be integers or math expressions, which are evaluated using `numexpr.evaluate()`.

(port-slicing)=

### Port slicing

You can also slice a port, to use some bits of the port as a signal that belongs to an interface.
The example below means:

`Port m_axi_bid of the IP core is 36 bits wide. Use bits 23..12 as the BID signal of AXI master named m_axi_1`

```yaml
m_axi_1:
    interface: AXI
    mode: master
    signals:
        in:
            BID: [m_axi_bid, 35, 0, 23, 12]
```

(interface-description-files)=

## Interface Description files

Topwrap can use predefined interfaces which are described in YAML-formatted files.
The interfaces you use don't have to be predefined, but it's possible to perform checks
on whether all the mandatory signals are connected, when you use an interface definition.

You can see an example file below:

```yaml
name: AXI4Stream
port_prefix: AXIS
signals:
    required:
        - TVALID
        - TDATA
        - TLAST
        - TREADY
    optional:
        - TID
        - TDEST
        - TKEEP
        - TSTRB
        - TUSER
```

The name of an interface has to be unique. We also specify a prefix which will be used as a shortened identifier.
