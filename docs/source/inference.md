# Interface mapping and inference

## Interface mapping

Topwrap supports adding additional interfaces to modules which didn't originally have them. To
facilitate this, mapping files, which describe what interfaces to add to what modules are used.
These mappings describe which module ports (or smaller parts thereof) correspond to what interface
signals, and what the resulting interfaces should be named.

### Mapping files

An example mapping file, adding an AXI4 interface to a module, looks like this:

```yaml
modules:
  - id:
      name: some_ip_core
      vendor: some_vendor
      library: some_library
    interfaces:
      M_AXI:
        interface:
          name: AXI4
        mode: MANAGER
        signals:
          awaddr: M_AXI_awaddr
          awlen: M_AXI_awlen
          # ...
```

At the top level, there is a single key, `modules`, which contains a list of module mapping
definitions.

Each module has two keys:

 - `id`, which describes the identifier (name, vendor, and library), used to match this definition
   to a module. The vendor and library fields may be omitted and will use Topwrap's default values
   instead (`vendor` and `libdefault` respectively).
 - `interfaces`, which is a list of interfaces to be added to this module.

Each interface is described by an object with the following keys:

 - `interface`, which is the identifier of the interface definition, and behaves in the same way as
   the module's `id` key.
 - `mode`, which describes the mode of the interface, and may be either `MANAGER` or `SUBORDINATE`.
 - `signals`, which is a list of signal assignments, each in the following format:
   `signal-name: port-selector`. In addition to selecting module ports, the port selector also
   supports selecting fields within structs, and bit slicing, with a SystemVerilog-like syntax, e.g.
   `some_port.some_field[1:0]`.

## Interface inference

In addition to explicit interface definitions, Topwrap also supports automatically inferring
interfaces from module ports based on the interface and module definitions.

Inference can be performed on groups of module ports, or fields of ports with struct types, and in
the latter case, it also supports ports that are one-dimensional arrays of structs, creating
separate interfaces for each array element.

The inference process is done in two steps. First, Topwrap finds all groups which might form an
interface. For module ports, this is done by finding common prefixes in port names. For structures,
all struct members (recursively including members of members) of a port are considered to be within
one group, named after the port.

Additionally, the inference logic accepts grouping hints, which describe which groups should be
merged together, and what the resulting group should be called. This is particularly useful in
conjunction with the struct-based inference, as usually there are separate ports for the input and
output signal structs, which need to be considered together to form a full interface. For example,
modules found in [`pulp-platform/axi`](https://github.com/pulp-platform/axi) have two ports for each
AXI interface: `req_i/o` and `resp_o/i`, each being a struct which contains all the signals.

When specified on the command line, grouping hints use the following syntax:
`old1,old2,...,oldN=new`. Whitespace between names and commas and the equal sign is ignored. Group
names must be non-empty. For example, the grouping hints for `axi_cdc` would look like this:
`src_req_i,src_resp_o=src` and `dst_req_o,dst_resp_i=dst`.

The second step is checking which interfaces fit which groups, and ranking how good of a fit they
are. Then, interface modes are determined based on port directions, and finally, candidate
assignments are applied, going from best to worst. If a port is used by two or more interfaces, the
higher scoring one takes precedence, and the lower scoring interfaces are ignored.

Finally, after the inference is done, a mapping is produced.
