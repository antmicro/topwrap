# Internal Representation

Topwrap uses a custom object hierarchy, further called "internal representation" or "IR", in order to store block design and related data in memory and operate on it.

## Class diagram

```{mermaid} ../../build/ir_classes.mmd
:alt: Internal Representation class diagram
:zoom:
```

## Frontend & Backend

The `Frontend` based classes converts external formats, such as SystemVerilog, VHDL or KPM into the IR.
Complementarily, the `Backend` based classes convert our IR into external formats.

The reason for separating the logic like this is to be able to easily add support for multiple fronteds and backends formats and make them interchangeable.

### API interface

```{eval-rst}
.. automodule:: topwrap.frontend.frontend
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

```{eval-rst}
.. automodule:: topwrap.backend.backend
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Module

```{eval-rst}
.. automodule:: topwrap.model.module
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Design

```{eval-rst}
.. automodule:: topwrap.model.design
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Interface

```{eval-rst}
.. automodule:: topwrap.model.interface
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Interface mapping and inference

### Port selector

```{eval-rst}
.. automodule:: topwrap.model.inference.port
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

### Mapping

```{eval-rst}
.. automodule:: topwrap.model.inference.mapping
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

### Inference

```{eval-rst}
.. automodule:: topwrap.model.inference.inference
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Connections

```{eval-rst}
.. automodule:: topwrap.model.connections
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## HDL Types

```{eval-rst}
.. automodule:: topwrap.model.hdl_types
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Interconnects

```{eval-rst}
.. automodule:: topwrap.model.interconnect
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Miscellaneous

```{eval-rst}
.. automodule:: topwrap.model.misc
    :members:
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

(sliced_vs_independent)=
## A note on "sliced" vs. "independent" signals

There is specific terminology used in Topwrap in the context of interface signals.
An interface is a collection of signals, each one being either `sliced` or `independent`.
A `sliced` signal exists as a plain external port in `Module.ports`, either the entire port, or some arbitrary slice of it and is just a mapping for Topwrap to know that such a plain port actually realizes a specific signal of some defined interface.

For example, if the user had an IP core written in pure Verilog that used the AHB interface for data exchange and control, it would most likely have all AHB signals (`haddr`, `htrans`, `hresp`, etc.) present as individual external ports on it:

```verilog
module custom_core (
    input  wire [31:0] haddr,
    input  wire [1:0]  htrans,
    output wire        hresp,
    ...
);

endmodule
```

If such a core was parsed into Topwrap's internal representation, each such port would end up in `Module.ports`.
Clearly though, all of these ports are actually realizing specific signals of the AHB interface. To store that information clearly in the IR, an `Interface` instance should be created and added to `Module.interfaces`.
During the creation of this interface instance, the `Interface.signals` field needs to be filled with the mapping of each `InterfaceSignal` from the AHB's `InterfaceDefinition` to a `ReferencedPort` referencing the plain port from `Module.ports`.
Now each backend will know that despite there being an interface instance on this module, all of its signals are in reality just plain ports and when such a module is used in a design, appropriate code will be generated to interact with these ports.
This situation, where an `InterfaceSignal` is mapped to a concrete plain port in the module, is called a "sliced" signal.

Now there is another type of a signal realization called an "independent" signal.
Independent signals are not, and cannot be mapped to plain ports.
They are transparent and get automatically connected to each other just by the action of connecting two interface instances together.
This situation naturally corresponds to using the `interface` construct in SystemVerilog:

```SystemVerilog
interface AHB_intf;
    logic [31:0] haddr,
    logic [1:0]  htrans,
    logic        hresp,
    ...
endinterface

module custom_core (
    AHB_intf ahb_sub,
    ...
);

endmodule
```

In the above example, the AHB interface is now explicit in the module definition itself.
The individual signals still exist, but are enclosed in the interface instance and will get automatically connected in case two such interface instances are connected.
There is still a need to store that interface in `Module.interfaces`, but now there doesn't exist any plain port that the interface signals would map onto, thus instead of an `InterfaceSignal` mapping to a `ReferencedPort` in the IR, it's mapped to `None` instead.
With that, the backends will know that this signal is represented by the interface instance itself and generate appropriate code.

Generally, in a single IR `Interface` all signals are either "sliced" or "independent", but a situation where majority of the signals are independent and a few are sliced or vice-versa is entirely possible and should appropriately handled by a specific backend.
