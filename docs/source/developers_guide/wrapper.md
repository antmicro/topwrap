# Wrapper

{class}`~topwrap.wrapper.Wrapper` is an abstraction over entities that have ports - examples include IP cores written in Verilog/VHDL, cores written in Amaranth and hierarchical collections for these that expose some external ports.
Subclasses of this class have to supply implementation of property {meth}`~topwrap.wrapper.Wrapper.get_ports` that has to return a list of all ports of the entity.

```{eval-rst}
.. autoclass:: topwrap.wrapper.Wrapper
   :members:

   .. automethod:: __init__
```
