(interconnect-generation)=
# Interconnect generation

Generating interconnects is an experimental feature of topwrap.
With a specification of which interfaces are masters or slaves and their address ranges, topwrap is able to automatically generate an interconnect conforming to this description. Currently supported interconnect types are:
- Wishbone round-robin

## Format

The format for describing interconnects is specified below. `interconnects` key must be a direct descendant of the `design` key in the design description.

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

    # specify interconnect parameters - interconnect-type-dependent (see "Interconnect params" section):
    params:
      {param_name1}: param_value1
      ...

    # specify masters and their interfaces connected to the bus
    masters:
    {master1_name}:
      - {master1_iface1_name}
      ...
    ...

    # specify slaves, their interfaces connected to the bus and their bus parameters
    slaves:
    {slave1_name}:
      {slave1_interface1_name}:
      # requests in address range [address, address+size) will be routed to this interface
      address: {start_address}
      size: {range_size}
      ...
    ...
```

## Interconnect params

Different interconnect types may provide different configuration options.
This section lists parameter names for available interconnects for use in the `params` section of interconnect specification.

### Wishbone round-robin

Corresponds to `type: wishbone_roundrobin`

- `addr_width` - bit width of the address line (addresses access `data_width`-sized chunks)
- `data_width` - bit width of the data line
- `granularity` - access granularity - smallest unit of data transfer that the interconnect is capable of transferring. Must be one of: 8, 16, 32, 64
- `features` - optional, list of optional wishbone signals, can contain: `err`, `rty`, `stall`, `lock`, `cti`, `bte`

## Limitations

Known limitations currently are:
- only word-sized addressing is supported (in other words - consecutive addresses access word-sized chunks of data)
- crossing clock domains is not supported
- down-converting (initiating multiple transactions on a narrow bus per one transaction on a wider bus) is not supported
- up-converting is not supported
