# User repositories
Repositories allow for easy loading packages with IP-cores.

You can add repositories to be loaded each time topwrap is ran by specifying them in configuration file.

It has to be located in one of the following locations:
```
topwrap.yaml
~/.config/topwrap/topwrap.yaml
~/.config/topwrap/config.yaml
```

Example contents of user config:
```
force_interface_compliance: true
repositories:
  - name: name of repo
    path: ~/path_to_repo/repo
```

Topwrap provides internal API for constructing repositories in python code which can be [found here](https://github.com/antmicro/topwrap/blob/main/topwrap/repo/user_repo.py#L144)

Structure of repository has to be as follows:
```
path_to_repository/
|───cores
|   |───someCore1
|   |   |───srcs
|   |   |   |   file1.v
|   |   |   design.yaml
|   |
|   |───someCore1
|       |───srcs
|       |   |   file1.v
|       |   design.yaml
|
|───interfaces(Optional)
|   interface1.yaml
|   interface2.yaml
```
Repository has two main catalogs: `cores` and `interfaces`. Inside `cores` each core has it's own catalog with it's design file and `srcs` where are stored verilog/VHDL files.

There is optional interfaces catalog where can be stored interfaces for cores.

Example User Repo can be found in [examples/user_repository](https://github.com/antmicro/topwrap/tree/main/examples/user_repository).
