# Using FuseSoC for automation

Topwrap uses [FuseSoC](https://github.com/olofk/fusesoc) (a package manager and a set of build tools for HDL code) to automate project generation and the build process. When `topwrap build` is used, it generates a [FuseSoC core file](https://fusesoc.readthedocs.io/en/stable/user/overview.html#fusesoc-s-basic-building-block-cores) along with the top-level wrapper.

A [template](https://github.com/antmicro/topwrap/blob/main/topwrap/templates/core.yaml.j2) for the core file is bundled with Topwrap (`templates/core.yaml.j2`).

[comment]: Is it worth putting the template here? We talk about editing it, so maybe it would make sense to have it visible here?

You may need to edit the file to change the backend tool, set additional `Hooks`, insert the FPGA part name and edit other parameters.
By default, {class}`topwrap.fuse_helper.FuseSocBuilder` searches for the template file in the directory you work in, meaning you must copy the template file into the project location.

After generating the core file, running FuseSoC will generate the bitstream and the program FPGA:

[comment]: Should we explain what a bitstream is somewhere?

```bash
fusesoc --cores-root build run project_1
```

This requires having a suitable backend tool in your `PATH` (e,g, [Vivado](https://www.xilinx.com/support/download.html).
