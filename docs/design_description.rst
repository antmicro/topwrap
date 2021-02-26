Design Description
==================

To create a complete, fully synthesizable design, a proper design file is needed.
It's used to specify to choose the IP cores for the project, set their parameters' values,
connect the IPs, and pick external ports (those which will be connected to physical I/O).

The structure is as below:

.. code-block:: yaml

    ips:
      {ip_instance_name}:
        file: {path_to_yaml_file_of_the_ip}
        module: {name_of_the_HDL_module}
        parameters:
          {param_name}: {param_value}
      ...

    ports: # specify ip1:port1 <-> ip2:port2 connections here
      {ip_instance_name}:
        {port_name} : [{ip_instance_name}, {port_name}]
        ...

    interfaces: # specify ip1:iface1 <-> ip2:iface2 connections here
      {ip_instance_name}:
        {iface_name} : [{ip_instance_name}, {iface_name}]
        ...

    external:
      {ip_instance_name}:
        - {port_name}
        ...

You can see an example design file in `examples` directory.
