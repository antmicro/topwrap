# IPWrapper class

{class}`~topwrap.ipwrapper.IPWrapper` provides an abstraction over a raw HDL source file.
Instances of this class can be created from the loaded IP-core YAML description.

It creates an Amaranth `Instance` object during elaboration, referencing a particular HDL module and appears as a module instantiation in the generated toplevel.
Ports and interfaces (lists of ports) can be retrieved via standard methods of {class}`~topwrap.wrapper.Wrapper`.
These are instances of {class}`~topwrap.amaranth_helpers.WrapperPort`s.


```{image} ../img/wrapper.png
```

```{eval-rst}
.. autoclass:: topwrap.ipwrapper.IPWrapper
   :members:

   .. automethod:: __init__
```
