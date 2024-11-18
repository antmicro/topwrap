(using-fusesoc)=
# Using FuseSoC for automation

Topwrap uses the [FuseSoC](https://github.com/olofk/fusesoc) package manager and build tools for HDL code to automate project generation and the build process. When `topwrap build` is used with the `--fuse` option, it generates a [FuseSoC core file](https://fusesoc.readthedocs.io/en/stable/user/overview.html#fusesoc-s-basic-building-block-cores) along with the top-level wrapper.

Topwrap assumes that you're using [Vivado](https://www.xilinx.com/support/download.html) for synthesis, bitstream generation and programming the FPGA.
You can change the default tool to something other than Vivado, by modifying the generated .core file.

## Additional build options

To enable the `.core` file generation supply the `--fuse/-f` flag to Topwrap build:

```bash
topwrap build -d design.yaml --fuse
```

If you have any additional directories with HDL sources or constraint files required for synthesis, you can specify them using the `--sources/-s` option.
Sources from these directories get appended to the `filesets.rtl.files` entry in the generated FuseSoC .core file.

```bash
topwrap build -d design.yaml -f --sources ./srcs_v -s ./srcs_vhd
```

If you're targeting a specific FPGA chip you can additionally specify its number using the `--part/-p` option.

The supplied part number is passed to the FuseSoC .core file to the `targets.default.tools.vivado.part` entry which finally ends up being supplied to [Vivado](https://www.xilinx.com/support/download.html) when you run FuseSoC and use the default target.
This can be any part number available to your local Vivado installation.

```bash
topwrap build -d design.yaml -f --part 'xc7z020clg400-3'
```

## .core file template

A [template](https://github.com/antmicro/topwrap/blob/main/topwrap/templates/core.yaml.j2) for the core file is bundled with Topwrap (`templates/core.yaml.j2`).

By default, {class}`topwrap.fuse_helper.FuseSocBuilder` searches for the template file in the directory you work in, meaning you must copy the template file into the project location. You may also need to edit the file to change the backend tool, set additional `Hooks`, add more targets, and edit other parameters.


## Synthesis

After generating the core file, you can run FuseSoC to generate the bitstream and program the FPGA:

```bash
fusesoc --cores-root build run {design_name}
```

This requires having the suitable backend tool that is specified in the `.core` file under `targets.default.tools` available in your `PATH` (e.g. [Vivado](https://www.xilinx.com/support/download.html)).
