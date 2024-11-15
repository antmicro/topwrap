(using-fusesoc)=
# Using FuseSoC for automation

Topwrap uses the [FuseSoC](https://github.com/olofk/fusesoc) package manager and build tools for HDL code to automate project generation and the build process. When `topwrap build` is used, it generates a [FuseSoC core file](https://fusesoc.readthedocs.io/en/stable/user/overview.html#fusesoc-s-basic-building-block-cores) along with the top-level wrapper.

A [template](https://github.com/antmicro/topwrap/blob/main/topwrap/templates/core.yaml.j2) for the core file is bundled with Topwrap (`templates/core.yaml.j2`).

By default, {class}`topwrap.fuse_helper.FuseSocBuilder` searches for the template file in the directory you work in, meaning you must copy the template file into the project location. You may also need to edit the file to change the backend tool, set additional `Hooks`, insert the FPGA part name and edit other parameters.

After generating the core file, running FuseSoC will generate the bitstream and the program FPGA:

```bash
fusesoc --cores-root build run project_1
```

This requires having a suitable backend tool in your `PATH` (e,g, [Vivado](https://www.xilinx.com/support/download.html).
