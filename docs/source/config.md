# Configuration

## Configuration file location

The configuration file must be located in one of the following locations:

```bash
topwrap.yaml
~/.config/topwrap/topwrap.yaml
~/.config/topwrap/config.yaml
```

## Configuration precedence

When multiple configuration files are present, the options are evaluated and overridden based on the location of the configuration file.
The precedence, from highest to lowest, is as follows:

- `topwrap.yaml` in the current working directory
- `~/.config/topwrap/topwrap.yaml` (user-specific configuration)
- `~/.config/topwrap/config.yaml` (fallback configuration)

For example, if `force_interface_compliance` is set to `true` in `~/.config/topwrap/config.yaml` but overridden to `false` in `topwrap.yaml`, the latter value will take precedence when running Topwrap in the directory containing `topwrap.yaml`.

### Merging strategies for configuration options

Different configuration options use different merging strategies when multiple configuration files are combined:

- **Override** (e.g. `force_interface_compliance`): The value from the higher-precedence file completely replaces the value in lower-precedence files.
- **Merge** (e.g. `repositories`): Values from all configuration files are merged.
  For example, repositories defined in `~/.config/topwrap/topwrap.yaml` are combined with repositories defined in `topwrap.yaml`.

## Available config options

The configuration file for Topwrap provides the following options:

- `force_interface_compliance`

  - Type: Boolean
  - Default: `false`
  - Merging strategy: Override

  This option enforces compliance with interface definitions when parsing HDLs.

  For more details, refer to [Interface compliance](description_files.md#interface-compliance).

- `repositories`

  - Type: Dictionary of `name: path`
  - Merging strategy: Merge
  - Specifies repositories to load, with each repository defined as an entry in which:
    - The key is the name of the repository.
    - The value is the [resource path](description_files.md#resource-path-syntax) to the repository.
  - Example of specifying multiple repositories:
    ```yaml
    repositories:
      name_of_repo: file:path_to_repo
      another_repo: file:/absolute/path/to/repo
    ```

  Repositories are used to package and load multiple IP cores and custom interfaces.

  For more information, refer to [User repositories](user_repositories.md).

### Example configuration file

Here is a sample configuration file used in the [hierarchy example](examples.md#hierarchy)

```yaml
force_interface_compliance: true
repositories:
  my_repo: file:./repo
```
