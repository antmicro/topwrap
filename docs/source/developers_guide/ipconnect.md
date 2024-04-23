# IPConnect class

{class}`~topwrap.ipconnect.IPConnect` provides means of connecting ports and interfaces of objects that are subclasses of {class}`~topwrap.wrapper.Wrapper`.
Since {class}`~topwrap.ipconnect.IPConnect` is a subclass of {class}`~topwrap.wrapper.Wrapper` itself, this means that it also has IO - ports and interfaces, and that multiple {class}`~topwrap.ipconnect.IPConnect`s can have their ports and interfaces connected to each other (or other objects that subclass {class}`~topwrap.wrapper.Wrapper`).

```{image} ../img/ipconnect.png
```

Instances of {class}`~topwrap.wrapper.Wrapper` objects can be added to an {class}`~topwrap.ipconnect.IPConnect` using {meth}`~topwrap.ipconnect.IPConnect.add_component` method:

```python
# create a wrapper for an IP
dma = IPWrapper('DMATop.yaml', ip_name='DMATop', instance_name='DMATop0')
ipc = IPConnect()
ipc.add_component("dma", dma)
```

Connections between cores can then be made with {meth}`~topwrap.ipconnect.IPConnect.connect_ports` and {meth}`~topwrap.ipconnect.IPConnect.connect_interfaces` based on names of the components and names of ports/interfaces:

```python
ipc.connect_ports("comp1_port_name", "comp1_name", "comp2_port_name", "comp2_name")
ipc.connect_interfaces("comp1_interface_name", "comp1_name", "comp2_interface_name", "comp2_name")
```

Setting ports or interfaces of a module added to {class}`~topwrap.ipconnect.IPConnect` as external with {meth}`~topwrap.ipconnect.IPConnect._set_port` and {meth}`~topwrap.ipconnect.IPConnect._set_interface` and allows these ports/interfaces to be connected to other {class}`~topwrap.wrapper.Wrapper` instances.
```python
ipc._set_port("comp1_name", "comp1_port_name", "external_port_name")
ipc._set_interface("comp1_name", "comp1_interface_name", "external_interface_name")
```

This is done automatically in {meth}`~topwrap.ipconnect.IPConnect.make_connections` method when the design is built based on the data from the YAML design description.

```{eval-rst}
.. autoclass:: topwrap.ipconnect.IPConnect
   :members:
   :private-members:

   .. automethod:: __init__
```
