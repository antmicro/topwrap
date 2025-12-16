# Constructing, configuring and loading repositories

By using Topwrap repositories, you can package and load different resources and use them in your designs.

You can specify the repositories to be loaded each time Topwrap runs, by listing them in a [configuration file](config.md#configuration-file-location) or by supplying a path to one or more repository directories using the `--repo` CLI argument.

A single repository can store multiple resource types.
Each supported type is associated with a subdirectory in the top-level repository directory.

A sample repository can be found in [examples/user_repository](https://github.com/antmicro/topwrap/tree/main/examples/user_repository).

## Supported resource types

### IP cores

- Path: `repo_dir/cores/`

The "Core" resource represents a self-contained IP core/module that can then be used as a component in a custom design created by the user.

Each core should be stored under its own subdirectory within the IP core resources directory and contain at least a description file named `.core.yaml`.
Other than that, the end user is free to store necessary RTL sources for the IP core in an arbitrary layout, even outside the repository directory itself, since all of them have to be described in the `.core.yaml` file anyways.

#### `.core.yaml` description file reference

```yaml
# The user-facing name for the IP core resource
# that is also used to identify it amongst other cores
name: antmicro_axilib_axireflector

# The name of the concrete top-level module that represents
# this core as it appears in the referenced sources.
top_level_name: axi_reflector

# Source files that have to be parsed by Topwrap in order
# to automatically extract information about the IP core.
# The definition of `top_level_name` module must be included
# somewhere in the sources as well.
sources:
  # The format of paths in this array follows the "Resource path syntax" specification:
  # https://antmicro.github.io/topwrap/description_files.html#resource-path-syntax
  - file:./srcs/axi_reflector.sv

  # Different types of sources are supported and recognised
  # automatically according to their extension
  - get:https://file.antmicro.com/abc123/axi_regs.yaml

  # (Recommended) The type of the resource can also be given explicitly
  - resource: file:./srcs/axi_pkg.svp
    # This identifies the frontend that will be used to parse this file
    type: systemverilog
```

### Interface definitions

- Path: `repo_dir/interfaces/`

This resource represents a custom definition of an interface that can be used to make connections between IP cores.

Each such definition is stored as a separate [interface description file](description_files.md#interface-description-files) under the `interfaces` subdirectory.

### Interface port mappings

- Path: `repo_dir/mappings/`

This resource represents a custom mapping from a module's ports to an interface.

Mappings are stored in [interface mapping files](inference.md#mapping-files) under the `mappings` subdirectory, with each file containing one or more mapping.

## CLI

### `topwrap repo init`
```bash
topwrap repo init [OPTIONS] REPO_NAME REPO_PATH
```

This command creates and initializes a new repository named `REPO_NAME` in a chosen `REPO_PATH`.

By default, it also adds the entry with the new repository into the local Topwrap [configuration file](config.md).
If the file does not exist, it gets created.
This behavior can be disabled using the `--no-config-update` CLI flag.

### `topwrap repo list`
```bash
topwrap repo list
```

This will print out names and paths of all repositories from which
resources are loaded and can be used in other Topwrap commands.

### `topwrap repo parse`
```bash
topwrap repo parse [OPTIONS] REPOSITORY SOURCES...
```

This command will parse all supported source files given in the `SOURCES` argument, extract IP cores from them, and save them in a repository given by the `REPOSITORY` argument.

:::{note}
When a directory path is given among the `SOURCES` argument, it gets recursively expanded and all nested files are extracted from it.
:::

To see the listing of all supported `OPTIONS`, see `topwrap repo parse --help`


## Using the open source IP cores library with Topwrap

Topwrap comes with built-in support for an extensive library of open source IP cores available through the [FuseSoC](https://github.com/olofk/fusesoc) package manager, which also serves as a build system. This library offers a wide range of reusable IP cores for various applications, enabling easy integration into Topwrap projects. Topwrap simplifies the process of accessing, downloading, and packaging these IP cores, making them readily available for local use in your designs.

To include an IP core from the open source library, there are two methods:

1. **Select the Desired Core**: Browse the available cores ([cores_export artifact](https://github.com/antmicro/topwrap/releases/tag/latest)).
2. **Download and build all available cores**: Use Topwrap's package management command:

```bash
  nox -s package_cores
```

This will download and parse all the cores from Fusesoc into `build/fusesoc_workspace/build/export/cores/`, making them accessible from within Topwrap.

You can learn more about Topwrap integration with FuseSoC [here](#fusesoc)
