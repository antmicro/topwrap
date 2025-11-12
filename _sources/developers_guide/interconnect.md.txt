# Interconnect

This document is about implementing new {class}`~topwrap.model.interconnect.Interconnect`, check [](../interconnect_gen.md) to read about `Interconnect` concept in Topwrap.

`Interconnect` is base class for all interconnects, it has 3 generic classes
that are used to represent params: {class}`~topwrap.model.interconnect.InterconnectParams`, `InterconnectManagerParams` and {class}`~topwrap.model.interconnect.InterconnectSubordinateParams`.
All new implementations of interconnect need to be placed in in `topwrap/interconnects/` and added to {const}`~topwrap.interconnects.types.INTERCONNECT_TYPES`.
Each interconnect needs to have implemented {class}`~topwrap.backend.generator.Generator`, refer to [](generator.md) to check how to implement one.

```{eval-rst}
.. automodule:: topwrap.model.interconnect.Interconnect
   :members:
   :private-members:
   :no-index:
```

```{eval-rst}
.. automodule:: topwrap.model.interconnect.InterconnectParams
   :members:
   :private-members:
   :no-index:
```

```{eval-rst}
.. automodule:: topwrap.model.interconnect.InterconnectSubordinateParams
   :members:
   :private-members:
   :no-index:
```

```{eval-rst}
.. automodule:: topwrap.model.interconnect.InterconnectManagerParams
   :members:
   :private-members:
   :no-index:
```

```{eval-rst}
.. automodule:: topwrap.interconnects.types.InterconnectTypeInfo
   :members:

.. autodata:: topwrap.interconnects.types.INTERCONNECT_TYPES
   :no-value:

```
