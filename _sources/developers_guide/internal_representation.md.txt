# Internal Representation

Topwrap uses a custom object hierarchy, further called "internal representation" or "IR", in order to store block design and related data in memory and operate on it.

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
