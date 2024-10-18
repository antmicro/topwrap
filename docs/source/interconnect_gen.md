(interconnect-generation)=
# Interconnect generation

Generating interconnects is an experimental feature in Topwrap, requiring a description of which interfaces are managers or subordinates and their address ranges. Topwrap then generates an interconnect conforming to the description provided. The currently supported interconnect types are:
- Wishbone round-robin

[comment]: could we show this interconnect somehow, maybe through a graphic visualising it? 

## Format

The format for describing interconnects is specified below. The `interconnects` key must be a direct descendant of the `design` key in the design description.

```yaml
interconnects:
  {interconnect1_name}:
    # specify clock and reset to drive the interconnect with
    clock: [{ip_name, clk_port_name}]
    reset: [{ip_name, rst_port_name}]
    # alternatively you can specify a connection to an external interface:
    # clock: ext_clk_port_name
    # reset: ext_rst_port_name

    # specify interconnect type
    type: {interconnect_type}

    # specify interconnect parameters - interconnect-type-dependent (see "Interconnect parameters" section):
    parameters:
      {parameters_name1}: parameters_value1
      ...

    # specify managers and their interfaces connected to the bus
    manager:
    {manager1_name}:
      - {manager1_interface1_name}
      ...
    ...

    # specify subordinates, their interfaces connected to the bus and their bus parameters
    subordinate:
    {subordinate1_name}:
      {subordinate1_interface1_name}:
      # requests in address range [address, address+size) will be routed to this interface
      address: {start_address}
      size: {range_size}
      ...
    ...
```

## Interconnect parameter names

Different interconnect types may provide for different configuration options.
This section lists parameter names for available interconnects, usable in the `parameters` section of the interconnect specification.

### Wishbone round-robin

[comment]: Is it sensible here to explain what wishbone round-robin is? For me, I have no idea what it is by reading these docs. 

Corresponds to `type: wishbone_roundrobin`

- `addr_width` - bit width of the address line (addresses access `data_width`-sized chunks)
- `data_width` - bit width of the data line
- `granularity` - access granularity - smallest unit of data transfer that the interconnect is capable of transferring. Must be one of: 8, 16, 32, 64
- `features` - optional, list of optional wishbone signals, can contain: `err`, `rty`, `stall`, `lock`, `cti`, `bte`

## Known limitations

The currently known limitations are:
- only word-sized addressing is supported (in other words - consecutive addresses can only access word-sized chunks of data)
- crossing clock domains is not supported
- down-converting (initiating multiple transactions on a narrow bus per one transaction on a wider bus) is not supported
- up-converting is not supported
