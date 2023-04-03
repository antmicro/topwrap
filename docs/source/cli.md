# Command-line Interface

## Building design

To run Topwrap, use:

```
python -m fpga_topwrap build --design project.yml
```

Where `project.yml` should be your file with description of the top module.

You can specify a directory to be scanned for additional sources:

```
python -m fpga_topwrap build --sources src --design project.yml
```

To implement the design for a specific FPGA chip, provide the part name:

```
python -m fpga_topwrap build --sources src --design project.yml --part 'xc7z020clg400-3'
```

(generating-ip-yamls)=

## Generating IP core description YAMLs

You can also use Topwrap to generate ip core description yamls from HDL sources,
that can be later used in your `project.yml`:

```
python -m fpga_topwrap parse [HDL_FILES]
```

In HDL source files, ports that belong to the same interface (e.g. wishbone or AXI),
have often a common prefix, which corresponds to the interface name. If such naming
convention is followed in the HDL sources, Topwrap can also divide ports into user-specified
interfaces, or automatically deduce interfaces names when generating yaml file:

```
python -m fpga_topwrap parse --iface wishbone --iface s_axi [HDL_FILES]

python -m fpga_topwrap parse --iface-deduce [HDL_FILES]
```

To get help, use:

```
python -m fpga_topwrap [build|parse] --help
```
