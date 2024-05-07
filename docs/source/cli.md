# Command-line Interface

## Building design

To run Topwrap, use:

```
python -m topwrap build --design project.yml
```

Where `project.yml` should be your file with description of the top module.

You can specify a directory to be scanned for additional sources:

```
python -m topwrap build --sources src --design project.yml
```

To implement the design for a specific FPGA chip, provide the part name:

```
python -m topwrap build --sources src --design project.yml --part 'xc7z020clg400-3'
```

(connect-topwrap-to-pm)=

## Connect Topwrap to Pipeline Manager

If you want to use Pipeline Manager as a UI for creating block design, you need to:

1. Build and run Pipeline Manager server application.

```
python -m topwrap kpm_build_server
python -m topwrap kpm_run_server
```

2. Run Topwrap's client application, that will connect to a running Pipeline Manager server app.

```
python -m topwrap kpm_client [-h ip_addr] [-p port] FILES
```

Topwrap will then try to connect to the server running on `ip_addr:port` and send a specification generated from `FILES`, which should be IP core description yamls.

If `-h` or `-p` options are not specified, ip address `127.0.0.1` and port `9000` will be chosen by default.

(generating-ip-yamls)=

## Generating IP core description YAMLs

You can also use Topwrap to generate ip core description yamls from HDL sources,
that can be later used in your `project.yml`:

```
python -m topwrap parse HDL_FILES
```

In HDL source files, ports that belong to the same interface (e.g. wishbone or AXI),
have often a common prefix, which corresponds to the interface name. If such naming
convention is followed in the HDL sources, Topwrap can also divide ports into user-specified
interfaces, or automatically deduce interfaces names when generating yaml file:

```
python -m topwrap parse --iface wishbone --iface s_axi HDL_FILES

python -m topwrap parse --iface-deduce HDL_FILES
```

To get help, use:

```
python -m topwrap [build|kpm_client|parse] --help
```
