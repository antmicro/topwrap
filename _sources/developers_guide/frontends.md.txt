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

## Error handling

A frontend raises `FrontendParseException` when its input is malformed or invalid.
The `approach` parameter selects how errors are handled: `strict` (the default) raises on errors, while `best_effort` logs them and returns IR that may be incomplete, for example to fix it manually or to work around a false positive.
Frontends that do not support `best_effort` behave as with `strict`.

## Frontends

### SystemVerilogFrontend

SystemVerilogFrontend class is used to parse System Verilog and Verilog files.
It is mainly used for adding modules to a repo, connected by Topwrap in a design.yaml.
It supports both `strict` and `best_effort` approaches.

The default `strict` approach raises `FrontendParseException` when the parser reports at least one error.
Warnings in module headers are logged, but do not cause an exception.
The `best_effort` approach does not raise `FrontendParseException` for parser errors.
Instead, it logs them and returns the IR recovered by Slang.
The returned IR may be incomplete or invalid and should be treated as a starting point for manual correction, not as a validated design.

The current diagnostic classification is:

| Input condition | `strict` | `best_effort` |
| --- | --- | --- |
| Syntax or semantic diagnostic in a module header | Raises `FrontendParseException` | Logs an error and returns recovered modules when possible |
| Missing included file (`\`include`) | Raises `FrontendParseException` | Logs an error and returns recovered modules when possible |
| Syntax error, undeclared identifier or instance of an unknown module in a module body | Raises `FrontendParseException` | Logs an error and returns recovered modules when possible |
| Diagnostics originating from macros or preprocessed locations in a header | Logs a warning and returns recovered modules when possible | Logs a warning and returns recovered modules when possible |
| Other diagnostics in a module body | Ignored by this classifier; returns recovered modules when possible | Ignored by this classifier; returns recovered modules when possible |

Instances of modules passed to the frontend in `modules` are not reported as unknown.

In particular, `best_effort` does not create a valid black-box component for an unknown module instance.
The containing module can still be returned, but its `design` may be `None` or may not contain the unresolved instance.
Similarly, syntax recovery can produce a module with missing ports or other incomplete IR.
Callers using `best_effort` should therefore validate the returned modules, ports, interfaces, designs, and connections before using or storing them.

### KpmFrontend

KpmFrontend class is used to parse KPM-specific files.
It is mainly used for getting a design from a GUI.

### YamlFrontend

YamlFrontend class is used to parse design.yaml and module.yaml files.
It follows a format specified in [design description](../description_files.md#design-description).

### IpXactFrontend

IpXactFrontend class is used to parse existing IP-XACT files the same way as SystemVerilogFrontend. Not all tags defined in the 2022 specification are supported.
This frontend supports parsing `component`, `design` and `abstractionDefinition` root tags. Supported features are:
 - `VLNV`, `parameters`, `ports` and `busInterfaces` in `component` root tag. `views` tag is unused and only one `designConfigurationInstantiation` is supported. Only one `componentInstantiation` tag is supported.
 - `componentInstances`, `adHocConnections` and `interconnections` in `design` root tag.
 - `ports`, with support for only `logicalName`, `onTarget` and `onInitiator` in `port` in `abstractionDefinition` root tag.
