IPWrapper class
===============

:class:`IPWrapper` is the main class used to instantiate an IP Core and generate HDL wrapper.
It's used to standardize names of ports that belong to interfaces to ease connecting multiple IPs.


.. py:class:: IPWrapper

    .. py:method:: __init__(self, yamlfile, ip_name, top_name=None)

        :param yamlfile: name of the file with :ref:`IP description <ip_description>`
        :type yamlfile: str
        :param ip_name: name of the HDL module to be wrapped
        :type ip_name: str
        :param top_name: name of the generated top module. Defaults to ``top_name + '_top'``
        :type top_name: str

    .. py:method:: get_ports(self)

        Return a list of all ports that belong to this IP

        :returns: List[WrapperPort]

    .. py:method:: get_ports_of_interface(self, iface_name)

        Return a list of ports of specific interface

        :param iface_name: name of the interface
        :type iface_name: str
        :returns: List[WrapperPort]
        :raises ValueError: if such interface doesn't exist

    .. py:method:: get_port_by_name(self, name)

        Given the name of a port, return the port

        :param name: name of a port
        :type name: str
        :returns: WrapperPort
        :raises ValueError: if such port doesn't exist

    .. py:method:: get_port_names(self)

        Return a list of names of all ports of this ip

        :returns: List[str]

    .. py:method:: get_port_names_of_interface(self, iface_name)

        return a list of names of ports that belong to specific interface

        :param iface_name: name of an interface
        :type iface_name: str
        :returns: List[str]
        :raises ValueError: if such interface doesn't exist

    .. py:method:: set_parameters(self, params)

        Set values of parameters defined in HDL source file (for example `generic` in VHDL)

        :param params: names and values of the parameters ``{name1: val1, name2: val2, ...}``
        :type params: dict

    .. py:method:: _create_ports(self, yamlfile)

        Initialize object attributes with data found in the yamlfile describing an IP Core.
        This method fills ``self._ports`` with ``WrapperPorts`` objects for each port of the IP
        and assigns interfaces to ports which belong to them.

        :param yamlfile: name of a YAML file with IP description
        :type yamlfile: str
        :raises ValueError: when interface compliance is violated, e.g. the interfaces which
            were used don't match the predefined interfaces

    .. py:method:: _set_parameter(self, name, value)
    
        Function used by :py:func:`set_parameters` to set a value of individual parameter
            of an IP Core defined in HDL source.

        :param name: name of the parameter
        :type name: str
        :param value: value of the parameter
