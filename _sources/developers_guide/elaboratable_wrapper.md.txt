# ElaboratableWrapper class

{class}`~topwrap.elaboratable_wrapper.ElaboratableWrapper` encapsulates an Amaranth's Elaboratable and exposes an interface compatible with other wrappers which allows making connections with them.
Supplied elaboratable must contain a `signature` property and a conforming interface as specified by [Amaranth docs](https://amaranth-lang.org/rfcs/0002-interfaces.html).
Ports' directionality, their names and widths are inferred from it.

```{eval-rst}
.. autoclass:: topwrap.elaboratable_wrapper.ElaboratableWrapper
   :members:

   .. automethod:: __init__
```
