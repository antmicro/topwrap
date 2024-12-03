# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Automatically generated YAML files are now more concise thanks to some arrays being serialized inline, instead of each element always occupying its own line
- Added "IP Cores", "Externals", and "Constants" layers to the GUI which you can hide/show from the settings
- Nox session for downloading and packaging FuseSoc libraries
- Support Python 3.13 and dropped support for Python 3.8
- Added to config option for choosing a location where KPM server should be built
- All in one command `topwrap gui` for building, starting the KPM server and connecting the client to it.
- Automatic dataflow saving with each change to the graph in KPM. This ensures that the state is preserved when the page is reloaded.

### Changed

- All YAML files internal to Topwrap (examples, tests, built-in repo) now only use the `.yaml` extension
- Default location for built KPM server from `./build/` to `$XDG_CACHE_HOME/topwrap/kpm_build`

### Fixed

- Resolved an issue where IP Core node names in the GUI were parsed from the yaml description file name.
- Resolved an issue with YAML files produced by `topwrap parse`, where unnecessary double hyphens (`--`) appeared in signal definitions
- Changed how validation is done in topwrap in order to support hierarchical designs and check for more errors while creating design

## [0.1.0] - 2024-09-27

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
