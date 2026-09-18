# Frontend

Frontend is a class that transforms a specific format into IR. There are multiple frontends:
 - SystemVerilogFrontend class supports SystemVerilog and Verilog files
 - KpmFrontend class supports Pipeline Manager files
 - YamlFrontend class supports YAML files
 - IpXactFrontend class supports IP-XACT 2022 files

Frontends may be initialized with predefined modules and interfaces, which are
used to resolve references while parsing. Parsed modules are returned in
`FrontendParseOutput`, including modules whose identifiers match predefined
modules. The handling of interfaces in `FrontendParseOutput` differs between
frontends: `SystemVerilogFrontend` returns parsed or reused interface
definitions, `IpXactFrontend` returns interface definitions parsed from
`abstractionDefinition` files, while `YamlFrontend` and `KpmFrontend` only use
predefined interfaces during parsing and do not return them. `AutomaticFrontend`
preserves the behavior of the frontend it delegates to.

## SystemVerilogFrontend

SystemVerilogFrontend class is used to parse System Verilog and Verilog files.
It is mainly used for adding modules to a repo, connected by Topwrap in a design.yaml.

## KpmFrontend

KpmFrontend class is used to parse KPM-specific files.
It is mainly used for getting a design from a GUI.

## YamlFrontend

YamlFrontend class is used to parse design.yaml and module.yaml files.
It follows a format specified in [design description](#design-description).

## IpXactFrontend

IpXactFrontend class is used to parse existing IP-XACT files the same way as SystemVerilogFrontend. Not all tags defined in the 2022 specification are supported.
This frontend supports parsing `component`, `design` and `abstractionDefinition` root tags. Supported features are:
 - `VLNV`, `parameters`, `ports` and `busInterfaces` in `component` root tag. `views` tag is unused and only one `designConfigurationInstantiation` is supported. Only one `componentInstantiation` tag is supported.
 - `componentInstances`, `adHocConnections` and `interconnections` in `design` root tag.
 - `ports`, with support for only `logicalName`, `onTarget` and `onInitiator` in `port` in `abstractionDefinition` root tag.
