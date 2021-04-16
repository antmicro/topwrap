IPConnect class
===============

Topwrap uses :class:`IPConnect` to encapsulate IP Cores in a module, and connect their wires and interfaces.

After the object is created, IPs can be added using :code:`add_ip` method:

.. code-block:: python

    # create a wrapper for an IP
    dma := IPWrapper('DMATop.yaml', ip_name='DMATop'),

    ipc = IPConnect()
    ip.add_ip(dma)
    
    # add other IPs


IPs are connected using :code:`make_connections` function.
Ports can be set as external input/output with :code:`make_external_ports` and retrieved with :code:`get_ports`.
For a wider example of using the :class:`IPConnect` see :ref:`Getting Started <getting_started>`

.. py:class:: IPConnect

    .. py:method:: __init__(self)

    .. py:method:: add_ip(self, ip: IPWrapper)

        Add a new IPWrapper object, allowing to make connections with it.

    .. py:method:: connect_ports(self, port1_name: str, ip1_name: str, port2_name: str, ip2_name: str)

        Connect ports of IPs that were previously added to this Connector

        :raises ValueError: if any of the IPs doesn't exist

    .. py:method:: connect_interfaces(self, iface1: str, ip1_name: str, iface2: str, ip2_name: str)

        Make connections between all matching signals of the interfaces

        :raises ValueError: if any of the IPs doesn't exist

    .. py:method:: _set_port(self, ip, port_name: str)

        Set port specified by name as an external port

        :param ip: IP which holds the I/O port
        :type ip: IPWrapper
        :raises ValueError: if such port doesn't exist

    .. py:method:: get_ports(self)

        Return a list of external ports of this module

    .. py:method:: _set_unconnected_ports(self)

        Create signals for unconnected ports to allow using them as external.
        This is essential since ports that haven't been used have no signals
        assigned to them.

    .. py:method:: make_connections(self, ports, interfaces)

        Make connections between IPs using the names of ports and names of interfaces matched with IPs.
        `Ports` and `interfaces` are dicts structured as follows::

            {ip_name: 
              {port_name: (ip_name2, port_name2)}
              ... }
             ...

    .. py:method:: build(self, build_dir='build', template=None, sources_dir=None,
              top_module_name='project_top', part=None):

        Generate a complete synthesizable project, including all the source files and a core file.


       :param build_dir: name of the output directory
       :param template: name of the core file template
       :param sources_dir: directory to be scanned for additional sources
       :param part: FPGA part name
