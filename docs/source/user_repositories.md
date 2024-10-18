# Constructing, configuring and loading repositories

By using Topwrap repositories, it is easy to package and load multiple IP cores and custom interfaces. You can specify the repositories to be loaded each time Topwrap runs by listing them in a configuration file. The file must be located in one of these locations:
```
topwrap.yaml
~/.config/topwrap/topwrap.yaml
~/.config/topwrap/config.yaml
```

Sample user configuration file :
```
force_interface_compliance: true
repositories:
  - name: name_of_repo
    path: ~/path_to_repo/repo
```

Topwrap provides an internal API for constructing repositories in Python code, [found here](https://github.com/antmicro/topwrap/blob/main/topwrap/repo/user_repo.py)

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
<!--question about filenames - in some places, we have .yaml (like here) and in some places .yml, should it be standardised? Or are these different things?-->
Each repository has two main directories: `cores` and `interfaces`. Inside `cores`, each core has it's own directory with a description file and the subdirectory `srcs` where Verilog/VHDL files are stored.

The `interfaces` directory is optional, and contains [interface description files](description_files.md).
<!--I want to link to `description_files.md#interface-description-files`, but it fails in CI - how to do this?-->

A sample user repository can be found in [examples/user_repository](https://github.com/antmicro/topwrap/tree/main/examples/user_repository).
