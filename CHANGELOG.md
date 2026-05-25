# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0]

### Added

- Added a new YAML field type that resolves and serializes paths relatively to the YAML file itself and supports loading remote files (`http(s)://` URLs) or files from a user repo with the given name
- While loading a design file (e.g. `topwrap kpm_client/build -d design.yaml`) all required IP Cores are now automatically parsed from the file and it's no longer required to provide them manually on the command line
- Automatically generated YAML files are now more concise thanks to some arrays being serialized inline, instead of each element always occupying its own line
- Added "IP Cores", "Externals", and "Constants" layers to the GUI which you can hide/show from the settings
- Nox session for downloading and packaging FuseSoc libraries
- Support Python 3.13 and dropped support for Python 3.8
- Added tests to CLI commands
- Added job for building and running the KPM server
- Added to config option for choosing a location where KPM server should be built
- All in one command `topwrap gui` for building, starting the KPM server and connecting the client to it.
- Automatic dataflow saving with each change to the graph in KPM. This ensures that the state is preserved when the page is reloaded.
- Extended SystemVerilog frontend to parse entire designs

### Changed

- The order of fields in generated KPM specifications are now deterministic
- Topwrap's builtin cores and interfaces have been repackaged into a user repository automatically loaded at start named `builtin`
- All YAML files internal to Topwrap (examples, tests, built-in repo) now only use the `.yaml` extension
- Default location for built KPM server from `./build/` to `$XDG_CACHE_HOME/topwrap/kpm_build/<kpm_commit_sha>/`
- The YAML file syntax has changed. Detailed information about the updated YAML format can be found in the documentation: https://antmicro.github.io/topwrap/description_files.html
  - The format of the design description YAML files has changed. To convert existing designs, the following changes are needed:
    - IP core instance parameters are now specified within the `ips` section, instead of a separate `parameters` section:
      ```yaml
      ips:
        some_core:
          ...
          parameters:
            SOME_PARAM: some_value
      ```
    - The `design` section has been removed and it's contents have moved.
      - `name`, `hierarchies`, `interconnects` are now specified at the top level of the YAML file
      - `ports`, `interfaces` are in a new `connections` section specified at the top level:
        ```yaml
        connections:
          ports:
            ...
          interfaces:
            ...
        ```
  - IP core YAML files and interface description YAML files have a new way of specifying identifiers:
    - The `name` key has been replaced by an `id` key, with the following structure:
      ```yaml
      id:
        name: some_ip_name
        vendor: some_ip_vendor
        library: some_ip_library
      ```
      - The `vendor` and `library` fields may be omitted, and default to `vendor` and `libdefault` respectively in that case.
  - The `port_prefix` key has been removed from interface description YAML files.
  - Sizes of interconnect subordinates (defined both in the interconnect and address maps) is now consistently specified in bytes (like the address). Previously, the meaning of `size` depended on the interconnect type (bytes for AXI, data width units for Wishbone RR).
- The way the user repository works has changed.
  - Instead of storing (System)Verilog sources directly for an IP core, repositories now store IP core YAML files describing the cores instead.
  - The `.core.yaml` description file has been removed.
  - The YAML file in each IP core directory has a uniform name: `module.yaml`.

### Fixed

- Resolving IP Core YAML paths defined in a design description now works relative to the location of the design file instead of the current working directory
    - Except when using the "Load file/Save file" options in the GUI
- Resolved an issue where IP Core node names in the GUI were parsed from the yaml description file name.
- Resolved an issue with YAML files produced by `topwrap parse`, where unnecessary double hyphens (`--`) appeared in signal definitions
- Changed how validation is done in topwrap in order to support hierarchical designs and check for more errors while creating design

## [0.6.0]

### Added

- Conversion of HDL sources into YAML IP core description files
    - Verilog and VHDL support
    - Interface recognition: AXI, AXI-Lite, AXI Stream, Wishbone
    - YAML-based description format for command-line use
- Design Assembly
    - Ability to assemble top-level designs from IP cores
    - Compliance checks for predefined interfaces
    - Generation of [FuseSoC](https://github.com/olofk/fusesoc) `.core` files
    - Use of [Amaranth HDL](https://github.com/amaranth-lang/amaranth) for final top-level generation
- GUI
    - Graphical interface powered by [Kenning Pipeline Manager](https://github.com/antmicro/kenning-pipeline-manager)
    - Drag-and-drop functionality for creating and connecting cores
    - Visualization of hierarchical designs
    - Validation and building of designs to identify potential issues
    - Conversion from YAML IP core/design to KPM specification/dataflow
- User Repository
    - Creation of custom libraries for reuse across projects
    - Dedicated directories for each core with its HDL and parsed IP core
    - Support for multiple HDL sources within a single repository entry
    - Built-in interface definitions
    - Automatic loading of IP core YAMLs from the user repositories
- Documentation
    - User documentation with examples and live previews
    - Developer's guide covering advanced topics and contribution guidelines
