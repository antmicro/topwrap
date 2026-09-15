# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0]

### Added

- A new, unified `topwrap generate` command replaces the now deprecated `build` command and folds SystemVerilog, FuseSoC, IP-XACT, KPM diagram and KPM specification generation into one invocation with `--fusesoc`, `--ipxact`, `--diagram` and `--specification` flags
- Added a FuseSoC-based library feature: `topwrap library add/update/list` registers a local directory or git repository of CAPI2 `.core` files, and IP cores can be referenced from a design by VLNV using a new `core:` key (as an alternative to the existing `file:` key). It supersedes the user-repository mechanism (`repo:`, `topwrap repo`, `--repo`), which is now deprecated
- Improved logging: colored console output and `INFO` as the default level, better structured
- An IP-XACT frontend and backend (IEEE 1685-2022), producing `component`, `design` and `abstractionDefinition`/`busDefinition` files, accessible via `topwrap generate --ipxact`
- An initial plugin system, integrated into the CLI and KPM client, with plugin metadata for designs and IP cores representable via a new `extensions:` section
- GUI:
  - Added a design YAML backend for exporting complete hierarchical designs (hierarchies, interconnects, memory maps, clock/reset domains) to design description YAML, and wired it up as an export/save action from the KPM GUI
  - Added a "positions YAML" mechanism that saves and restores the on-canvas positions of modules, externals, constants and interconnects set in the KPM GUI. A design YAML may reference one via an optional `positions:` field, which is loaded and saved automatically alongside the design
  - Added "Export IP" and "Hierarchy export" actions for exporting a selected subgraph, the ability to target arbitrary subgraphs, and a button to save the current design in-place
  - Added an option to disable specific KPM node layers when generating the dataflow
- Support for specifying filelists and include directories for HDL sources in IP core YAML files
- A `topwrap package` command for creating an IP description and optional library `.core` from HDL sources, filelists, include directories and preprocessor defines
- An `existing_iface_definitions` entry to `module.yaml`, letting an IP core declare interface definitions already present in the parsed HDL so they aren't regenerated
- Support for multidimensional ports (via a new `bound` property) in design/IP core YAML and in the IP-XACT frontend
- IP core YAML frontend/backend now records signal type information (e.g. struct types) and source `path` metadata, and reuses existing port definitions where possible when re-parsing
- Added support for connections between interconnects and external interfaces (YAML frontend and backend), and hierarchical SystemVerilog generation for interconnects in nested designs

### Changed

- Dropped Python 3.9 support; Python 3.10 is now the minimum supported version
- Interface `type:` references in `module.yaml` now use the same `Identifier` (VLNV) structure as IP core `id:` fields, instead of a plain name
- Reworked interface auto-exposure in the KPM client: interfaces are now automatically exposed/privatised by a new inference algorithm, manually toggling exposure by hand has been disabled, and dataflow validation now flags unexposed or incorrectly-exposed interfaces
- Reworked and extended the FuseSoC backend (clock and reset signals are now represented in generated IP YAMLs) and reorganized the generated build output directory layout
- Generated YAML/JSON output formatting improved and made more consistent (module parameters, inout exposure, hierarchies, KPM node config data), and generated JSON (e.g. KPM specs) is now indented for readability
- Installation instructions now recommend `uv` instead of raw `pip`

### Fixed

- VLNV key collisions in internal lookup dictionaries that could cause the wrong module/interface to be resolved
- Dropped/duplicated `version` fields in the KPM specification backend and dataflow frontend
- Vendor/library field parsing and inout-interface handling in the KPM validator, and made it look through all graphs instead of only the top one
- Incorrect array-size and port-type computations that could produce a string expression where a number was expected are fixed
- Signal widths for interface definitions had been missing from generated SystemVerilog output
- Hierarchical designs not failing anymore when a submodule shared its name with the toplevel module, and when a module name exceeded filesystem name limits
- Interface definitions that weren't present in the parsed HDL are generated (previously they were silently skipped)
- SystemVerilog generation for AXI interconnects when using external interfaces corrected
- The KPM GUI can now run under Bazel
- Malformed, hard-to-read CLI error messages for invalid design/IP-core YAML are improved

### Deprecated

- The user repository mechanism is deprecated and will be removed in 1.0. Users must switch to the new library mechanism
- `topwrap build` is deprecated and will be removed in 1.0. Users must switch to `topwrap generate`
- Deprecated commands are hidden from the CLI help texts, but still accessible

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
