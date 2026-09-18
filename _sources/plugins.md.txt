# Plugin Support

Topwrap uses a plugin mechanism to allow external software to customize or extend the capabilities of Topwrap.
Plugins take the form of Python modules.

## Ways to get plugins

There are two ways to get plugins, install and configure pre-existing plugins or build your own.

### Plugin repositories

Antmicro hosts plugins in [https://github.com/antmicro/topwrap-utils](https://github.com/antmicro/topwrap-utils).

### Building your own

Building plugins on your own requires insight into how Topwrap works.
You are encouraged to review the Developer's guide on [plugins](./developers_guide/plugins.md) and to use an [existing plugin](https://github.com/antmicro/topwrap-utils/tree/main/topwrap-renode-plugin) as a start-of point.

## Plugin configurations

Plugins are configured both at the IP-core level and the design level.
Both files provide a configurable property `extensions` that is used to pass options to the plugin.
See the chapter on [creating designs](./description_files.md) for more info about the format of configuration options.
Also review the documentation for each plugin, which will describe plugin-specific settings.
