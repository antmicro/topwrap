# Using FuseSoC for automation

Topwrap uses the [FuseSoC](https://github.com/olofk/fusesoc) package manager and build tools for HDL code to automate project generation and the build process. When `topwrap generate` is used with the `--fusesoc` option, it generates a [FuseSoC `.core` file](https://fusesoc.readthedocs.io/en/stable/user/overview.html#fusesoc-s-basic-building-block-cores) along with the top-level wrapper.

## Default tool for synthesis, bitstream generation and programming the FPGA

Topwrap assumes that you're using [Vivado](https://www.xilinx.com/support/download.html). You can change the default tool to something other than Vivado by modifying the generated `.core` file.

## Additional build options

To enable `.core` file generation, supply `--fusesoc` to `topwrap generate`:

```bash
topwrap generate design.yaml --fusesoc
```

If you have any additional directories with HDL sources or constraint files required for synthesis, you can specify them using the repeatable `--sources` option.
Sources from these directories get appended to the `filesets.rtl.files` entry in the generated FuseSoC `.core` file.

```bash
topwrap generate design.yaml --fusesoc --sources ./srcs_v --sources ./srcs_vhd
```

If you're targeting a specific FPGA chip, you can additionally specify its number using the `--part` option.

The supplied part number is passed to the FuseSoC `.core` file. It is included in the `targets.default.tools.vivado.part` entry, which is then supplied to [Vivado](https://www.xilinx.com/support/download.html) when you run FuseSoC and use the default target. This can be any part number available to your local Vivado installation.

```bash
topwrap generate design.yaml --fusesoc --part 'xc7z020clg400-3'
```

Library-backed IPs used by the design are emitted as dependencies of the generated core. FuseSoC therefore includes their own RTL filesets when it builds the design.

Use `--target-dir` to change the output root. The wrapper and `.core` file are written to its `src` subdirectory.

The generated core currently defines a default Vivado target. Edit the generated `.core` file if another tool, additional targets or hooks are required.

## Synthesis

After generating the `.core` file, you can run FuseSoC to generate the bitstream and program the FPGA:

```bash
fusesoc --cores-root build/src run {design_name}
```

This requires having a suitable backend tool that is specified in the `.core` file under `targets.default.tools` available in your `PATH` (e.g. [Vivado](https://www.xilinx.com/support/download.html)).
