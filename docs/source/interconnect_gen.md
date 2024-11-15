(interconnect-generation)=
# Interconnect generation

:::{warning}
Interconnect generation is an experimental feature.

Currently, creating and showing them is not possible in the Topwrap GUI. 
:::

Interconnects are a convenient feature that allows users to connect multiple interfaces together in a many-to-many topology, instead of the traditional one-to-one connection between a manager and a subordinate. This provides a method of transmitting data between multiple IP cores over a single interface connection in which the interconnect acts as a middle-man.

```{mermaid}
:alt: Interconnect topology diagram

%%{init: {'theme':'neutral'}}%%

flowchart TB;

m1[Manager 1] --> int[/<p style="margin: 1.5em 4em">Interconnect</p>\]
m2[Manager 2] --> int
mN[Manager 3, 4, 5 ...] --> int

%%mN@{ shape: st-rect }

int --> s1[Subordinate 1 <p style="font-size: 0.8em">Address: 0x0A</p>]
int --> s2[Subordinate 2 <p style="font-size: 0.8em">Address: 0x1A000</p>]
int --> sN[Subordinate 3, 4, 5... <p style="font-size: 0.8em">Address: 0x....</p>]

%%sN@{ shape: st-rect }
```

Each manager can talk to every subordinate connected to the interconnect.
Each connected subordinate must have a predefined address range so that the interconnect knows how to route data based on the address put up on the wire by a manager.

In order to generate an interconnect you have to describe its configuration in the [design description](#design-description) under the `interconnects` key in the following format:

(interconnect-format)=
## Format

The format for describing interconnects is specified below. The `interconnects` key must be a direct descendant of the `design` key in the [design description](#design-description).

```yaml
interconnects:
  {interconnect1_name}:
    # Specify clock and reset to drive the interconnect with
    clock: [{ip_name, clk_port_name}]
    reset: [{ip_name, rst_port_name}]
    # Alternatively you can specify a connection to an external port of this design:
    # clock: ext_clk_port_name
    # reset: ext_rst_port_name

    # Specify the interconnect type.
    # See the "Supported interconnect types" section below for available types
    # and their characteristics
    type: {interconnect_type}

    # custom parameter values for the specific interconnect type
    parameters:
      {parameters_name1}: parameters_value1
      ...

    # specify managers and their interfaces connected to the bus
    managers:
      {manager1_name}:
        - {manager1_interface1_name}
        ...
      ...

    # specify subordinates, their interfaces connected to the bus and their bus parameters
    subordinates:
      {subordinate1_name}:
        {subordinate1_interface1_name}:
          # requests in address range [address, address+size) will be routed to this interface
          address: {start_address}
          size: {range_size}
        ...
      ...
  ...
```
(supported-interconnect-types)=
## Supported interconnect types

(supported-interconnect-wishbone-roundrobin)=
### `wishbone_roundrobin`

This interconnect only supports Wishbone interfaces for managers and subordinates.
It supports multiple managers, but only one of them can drive the bus at a time (i.e. only one transaction can be happening on the bus at any given moment).
A round-robin arbiter decides which manager can currently drive the bus.

(supported-interconnect-wishbone-roundrobin-parameters)=
#### Parameters

- `addr_width` - bit width of the address line (addresses access `data_width`-sized chunks)
- `data_width` - bit width of the data line
- `granularity` - access granularity - the smallest unit of data transfer that the interconnect can transfer. Must be: 8, 16, 32, 64
- `features` - optional, list of optional wishbone signals, can contain: `err`, `rty`, `stall`, `lock`, `cti`, `bte`

(supported-interconnect-wishbone-roundrobin-limitations)=
#### Known limitations

The currently known limitations are:
- only word-sized addressing is supported (in other words - consecutive addresses can only access word-sized chunks of data)
- crossing clock domains, down-converting (initiating multiple transactions on a narrow bus per one transaction on a wider bus) and up-converting are not supported