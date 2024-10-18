# ElaboratableWrapper class

{class}`~topwrap.elaboratable_wrapper.ElaboratableWrapper` encapsulates an Amaranth's Elaboratable and exposes an interface compatible with other wrappers which allows for making connections with them.

The supplied elaboratable must contain the `signature` property and a conforming interface as specified by the [Amaranth docs](https://amaranth-lang.org/rfcs/0002-interfaces.html).

The names, directionality and widths of ports are inferred from it.

```{eval-rst}
.. autoclass:: topwrap.elaboratable_wrapper.ElaboratableWrapper
   :members:

   .. automethod:: __init__
```
