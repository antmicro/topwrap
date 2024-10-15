# Interface definition

Topwrap uses interface definition files for its parsing functionality.
These are used to match a given set of signals that appear in the HDL source with signals in the interface definition.

{class}`~topwrap.interface.InterfaceDefinition` is defined as a {class}`marshmallow_dataclass.dataclass` - this enables loading YAML structure into Python objects and performs validation (that the YAML has the correct format) and typechecking (that the loaded values are of correct types).


```{eval-rst}
.. autoclass:: topwrap.interface.InterfaceDefinition
   :members:

   .. automethod:: __init__
```

```{eval-rst}
.. autofunction:: topwrap.interface.get_interface_by_name
```
