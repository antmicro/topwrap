# Helpers

```{eval-rst}
.. py:class:: InterfaceDef

    Representation of a predefined interface.

    .. py:method:: __init__(self, name, prefix, signals)

        :param name: full name of the interface
        :param prefix: prefix used as a short identifier for the interface
        :param signals: lists of names of required and optional signals in a dict
        :type signals: ``{'required': [str], 'optional': [str]}``

```

```{eval-rst}
.. py:function:: get_interface_by_name(name: str)

    Retrieve a predefined interface definition by its name

    :returns: ``InterfaceDef`` object, or ``None`` if there's no such interface
```

```{eval-rst}
.. py:function:: get_interface_by_prefix(prefix: str)

    Retrieve a predefined interface definition by its prefix

    :returns: ``InterfaceDef`` object, or ``None`` if there's no such interface
```

```{eval-rst}
.. py:class:: Config

    Configuration class used to store global choices for behavior of Topwrap.

    .. py:method:: __init__(self, force_interface_compliance=False)

    A global instance named ``config`` is created initially.
    Users can toggle forcing compliance checks on interfaces:

    .. code-block:: python

        from fpga_topwrap.config import config

        config.force_interface_compliance = False


```

```{eval-rst}
.. py:function:: check_interface_compliance(iface_def, signals)

    Check if list of signal names matches the names in interface definition

    :returns: bool
```
