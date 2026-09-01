# Interface inference

:::{warning}
SystemVerilog modules with parameter types are not fully supported by inference. There is no way to
override default parameter values, and as such, you must create a wrapper module that has concrete
parameter values specified. Ports with non-parameterized types are unaffected by this.

This is particularly important to keep in mind when using modules that use ports with struct types,
since the types are likely realized using parameter types.
:::

In addition to explicit interface definitions, Topwrap also supports automatically inferring
interfaces from module ports based on the interface and module definitions. This can be done when
parsing SystemVerilog modules using `topwrap repo parse` by specifying the `--inference` flag.

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

When specified on the command line via the `--grouping-hint` argument (which can be specified
multiple times to add multiple hints), grouping hints use the following syntax:
`old1,old2,...,oldN=new`. Whitespace between names, commas, and the equal sign is ignored, and all
group names must be non-empty. For example, grouping hints arguments for `axi_cdc` would look like
this: `--grouping-hint=src_req_i,src_resp_o=src` and `--grouping-hint=dst_req_o,dst_resp_i=dst`.

The second step is checking which interfaces fit which groups, and ranking how good of a fit they
are. Then, interface modes are determined based on port directions, and finally, candidate
assignments are applied, going from best to worst. If a port is used by two or more interfaces, the
higher scoring one takes precedence, and the lower scoring interfaces are ignored.

You can limit which interface definitions are considered during inference using the
`--inference-interface` argument. The argument takes an interface definition name, and can be
specified multiple times. During inference, only interfaces with names matching the specified ones
will be considered. For example, to only attempt to infer `AXI4` and `AHB` interfaces, the arguments
would look like this: `--inference-interface AXI4` and `--inference-interface AHB`.
