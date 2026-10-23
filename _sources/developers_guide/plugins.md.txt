# Plugins

Plugins are Python modules that are installed in the same environment as Topwrap.
They must define an entry point in the `topwrap.plugins` group.
The entry point is a class that inherits from {class}`~topwrap.plugin.base.BasePlugin`.
`pyproject.toml` must contain the following:

```toml
[project.entry-points."topwrap.plugins"]
<plugin-name> = "<plugin-name>.<module-path>:<PluginBase-subclass>"
```

:::{important}
Plugin support is experimental and both the mechanism and API may change partially or completely between Topwrap versions.
:::

## Examples

Use an existing plugin as a base for developing your own: [github.com/antmicro/topwrap-utils](https://github.com/antmicro/topwrap-utils/tree/main/topwrap-renode-plugin).

## Plugin Base

By defining implementations for the various hooks defined by {class}`~topwrap.plugin.base.BasePlugin`, the plugin can modify or extend Topwrap's capabilities.
All methods are passed the current {class}`~topwrap.plugin.base.BuildContext` which contains the [internal representation](./internal_representation.md) of the design and other metadata.


```{eval-rst}
.. automodule:: topwrap.plugin.base
    :members: BasePlugin
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```

## Build Context

The {class}`~topwrap.plugin.base.BuildContext` exposes runtime metadata including the internal representation of the design.
It is **shared** between Topwrap and any loaded plugins.
Use the documentation on the [internal representation](./internal_representation.md) for insight into what the metadata represents.

```{eval-rst}
.. automodule:: topwrap.plugin.base
    :members: BuildContext
    :show-inheritance:
    :undoc-members:
    :member-order: bysource
```
