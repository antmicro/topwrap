Wrapper Port
===============

Class :class:`WrapperPort` is an extension to nMigen's :class:`Signal`.
It wraps a port, adding a new name and optionally slicing the signal.
It adds these attributes:

.. code-block:: python
    
    WrapperPort.internal_name     # name of the port in internal source to be wrapped
    WrapperPort.direction         # DIR_FANIN, DIR_FANOUT or DIR_NONE
    WrapperPort.interface_name    # name of the group of ports (interface)
    WrapperPort.bounds            # range of bits that belong to the port
                                  # and range which is sliced from the port 

See :ref:`Port slicing <port_slicing>` to know more about ``bounds``.

This is used in :code:`IPWrapper` class implementation and there should be no need to use :class:`WrapperPort` individually.

.. py:class:: WrapperPort(Signal)

    .. py:method:: __init__(self, bounds, name, internal_name, direction, interface_name)

        :param bounds[0:1]: upper and lower bounds of reference signal
        :param bounds[2:3]: upper and lower bounds of internal port,
            which are either the same as reference port,
            or a slice of the reference port

        :param name: a new name for the signal
        :param internal_name: name of the port to be wrapped/sliced
        :param direction: one of :py:class:`nmigen.hdl.rec.Direction`, e.g. ``DIR_FANOUT``
