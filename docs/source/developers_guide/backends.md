# Backend

Backend is a class that transforms IR into a specific output format. There are multiple backends:
 - SystemVerilogBackend class generates SystemVerilog top files
 - KpmBackend class generates Pipeline Manager files
 - IpCoreDescriptionBackend and DesignDescriptionBackend classes generate YAML files
 - IPXACTBackend class generates IP-XACT 2022 files

## SystemVerilogBackend

SystemVerilogBackend class is used to generate a SystemVerilog top wrapper from a design.
It is the backend used by `topwrap build`, see [Generating Verilog top files](getting_started.md#generating-verilog-top-files).

## KpmBackend

KpmBackend class is used to generate Pipeline Manager specification and dataflow files.
It is mainly used to export a design to the GUI.

## YAML backends

IpCoreDescriptionBackend and DesignDescriptionBackend classes are used to generate IP core description and design description YAML files, respectively.
They follow the format specified in [design description](description_files.md#design-description).

## IPXACTBackend

IPXACTBackend class is used to generate IP-XACT 2022 files from a design.
It produces `component`, `design` and `abstractionDefinition`/`busDefinition` files and relies on the `topwrap-ipxact-parser` library.
For interconnects it reuses the SystemVerilog generators, as different HDL backends may yield different IR modules.

This is the backend used by the `topwrap ipxact_gen` command, see [Generating IPXACT 2022 files](getting_started.md#generating-ipxact-2022-files).
For details on the IP-XACT format and the Topwrap to IP-XACT conversion, see the [IP-XACT format](developers_guide/ipxact-design.md) document.

### UNSPECIFIED interface type

Interfaces defined in module can have MANAGER, SUBORDINATE or UNSPECIFIED types.
This types are used to select direction of port.
IPXACT 2022 don't have ability to represent UNSPECIFIED type.
When IPXACTBackend encounters UNSPECIFIED type it will log warning and proceed as if it was MANAGER type.

### Elaborating parameters

Elaboration of parameters that are present in widths of ports and interfaces is not supported.
Generated IPXACT files can contain illegal widths, it is recommended to use `sed` to change them to selected values.
