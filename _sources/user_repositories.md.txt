# Packaging multiple files

Repositories allow for easy packaging and loading multiple IP-cores and custom interfaces.

You can specify repositories to be loaded each time topwrap is ran by listing them in a configuration file that should be located in one of the following locations:
```
topwrap.yaml
~/.config/topwrap/topwrap.yaml
~/.config/topwrap/config.yaml
```

Example contents of user config:
```
force_interface_compliance: true
repositories:
  - name: name_of_repo
    path: ~/path_to_repo/repo
```

Topwrap provides internal API for constructing repositories in python code which can be [found here](https://github.com/antmicro/topwrap/blob/main/topwrap/repo/user_repo.py)

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
Repository has two main directories: `cores` and `interfaces`.

Inside `cores` each core has it's own directory with it's description file and `srcs` where the verilog/VHDL files are stored.

The `interfaces` directory is optional, and contains interface description files.

Example User Repo can be found in [examples/user_repository](https://github.com/antmicro/topwrap/tree/main/examples/user_repository).
