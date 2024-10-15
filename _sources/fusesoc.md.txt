# FuseSoC

Topwrap uses FuseSoC to automate project generation and build process.
When `topwrap build` is invoked it generates a FuseSoC core file along with the top-level wrapper.

A template for the core file is bundled with Topwrap (`templates/core.yaml.j2`).
You may need to edit the file to change the backend tool, set additional `Hooks` and change the FPGA part name or other parameters.
By default, {class}`topwrap.fuse_helper.FuseSocBuilder` searches for the template file in the directory you work in, so you should first copy the template into the project's location.

After generating the core file you can run FuseSoC to generate bitstream and program FPGA:

```bash
fusesoc --cores-root build run project_1
```

This requires having the suitable backend tool in your `PATH` (Vivado, for example).
