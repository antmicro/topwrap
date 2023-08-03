# Wrapper Port

Class {class}`WrapperPort` is an extension to Amaranth's {class}`Signal`.
It wraps a port, adding a new name and optionally slicing the signal.
It adds these attributes:

```python
WrapperPort.internal_name     # name of the port in internal source to be wrapped
WrapperPort.direction         # DIR_FANIN, DIR_FANOUT or DIR_NONE
WrapperPort.interface_name    # name of the group of ports (interface)
WrapperPort.bounds            # range of bits that belong to the port
                              # and range which is sliced from the port
```

See {ref}`Port slicing <port-slicing>` to know more about `bounds`.

This is used in {code}`IPWrapper` class implementation and there should be no need to use {class}`WrapperPort` individually.

```{eval-rst}
.. autoclass:: fpga_topwrap.nm_helper.WrapperPort
   :members:

   .. automethod:: __init__
```
