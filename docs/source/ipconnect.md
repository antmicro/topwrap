# IPConnect class

Topwrap uses {class}`IPConnect` to encapsulate IP Cores in a module, and connect their wires and interfaces.

After the object is created, IPs can be added using {code}`add_ip` method:

```python
# create a wrapper for an IP
dma := IPWrapper('DMATop.yaml', ip_name='DMATop', instance_name='DMATop0'),

ipc = IPConnect()
ip.add_ip(dma)

# add other IPs
```

IPs are connected using {code}`make_connections` function.
Ports and interfaces can be set as external input/output/inout with {code}`make_external_ports_interfaces` and retrieved with {code}`get_ports`.
For a wider example of using the {class}`IPConnect` see {ref}`Getting Started <getting-started>`

```{eval-rst}
.. autoclass:: fpga_topwrap.ipconnect.IPConnect
   :members:

   .. automethod:: __init__
```
