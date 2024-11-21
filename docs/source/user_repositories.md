# Constructing, configuring and loading repositories

By using Topwrap repositories, you can package and load multiple IP cores along with custom interfaces.
You can specify the repositories to be loaded each time Topwrap runs by listing them in a [configuration file](config.md#configuration-file-location).
The file must be located in one of these locations:

```
topwrap.yaml
~/.config/topwrap/topwrap.yaml
~/.config/topwrap/config.yaml
```

Sample user configuration file:

```
force_interface_compliance: true
repositories:
  - name: name_of_repo
    path: ~/path_to_repo/repo
```

Topwrap provides an internal API for constructing repositories in [Python](https://github.com/antmicro/topwrap/blob/main/topwrap/repo/user_repo.py).

The structure of the repository is as follows:

```
path_to_repository/
|───cores
|   |───ipcore1
|   |   |───srcs
|   |   |   |   file1.v
|   |   |   file1.yaml
|   |
|   |───ipcore2
|       |───srcs
|       |   |   file2.v
|       |   file2.yaml
|
|───interfaces(Optional)
    |   iface1.yaml
    |   iface2.yaml
```

Each repository has two main directories: `cores` and `interfaces`.
Inside `cores`, each core has its own directory with a description file and the subdirectory `srcs` where Verilog/VHDL files are stored.
The `interfaces` directory is optional, and contains [interface description files](description_files.md#interface-description-files).

A sample user repository can be found in [examples/user_repository](https://github.com/antmicro/topwrap/tree/main/examples/user_repository).

## Using the open source IP cores library with Topwrap

Topwrap comes with built-in support for an extensive library of open source IP cores available through the [Fusesoc](https://github.com/olofk/fusesoc) package manager, which also serves as a build system. This library offers a wide range of reusable IP cores for various applications, enabling easy integration into Topwrap projects. Topwrap simplifies the process of accessing, downloading, and packaging these IP cores, making them readily available for local use in your designs.

To include an IP core from the open source library, there are two methods:

1. **Select the Desired Core**: Browse the available cores ([cores_export artifact](https://github.com/antmicro/topwrap/releases/tag/latest)).
2. **Download and build all available cores**: Use Topwrap's package management command:

```bash
  nox -s package_cores
```

This will download and parse all the cores from Fusesoc into `build/fusesoc_workspace/build/export/cores/`, making them accessible from within Topwrap.

You can learn more about Topwrap integration with Fusesoc [here](#fusesoc)
