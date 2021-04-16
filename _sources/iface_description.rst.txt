Interface Description files
===========================

Topwrap can use predefined interfaces which are descibed in YAML-formatted files.
The interfaces you use don't have to be predefined, but it's possible to perform checks
on whether all the mandatory signals are connected, when you use an interface definition.

You can see an example file below:

.. code-block:: yaml

    name: AXI4Stream
    port_prefix: AXIS
    signals:
        required:
            - TVALID
            - TDATA
            - TLAST
            - TREADY
        optional:
            - TID
            - TDEST
            - TKEEP
            - TSTRB
            - TUSER

The name of an interface has to be unique. We also specify a prefix which will be used as a shortened identifier.
