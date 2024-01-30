# FPGA Topwrap HDMI example setup

Copyright (c) 2021-2024 [Antmicro](https://antmicro.com)

This is an example on how to use [Topwrap](https://github.com/antmicro/topwrap) to build a complex, synthesizable design.

## Usage

Install Vivado and add it to your `PATH`.

### Generate bitstream for desired target:

Snickerdoodle Black:

<!-- name="snickerdoodle" -->
```
make snickerdoodle
```

Zynq Video Board:

<!-- name="zvb" -->
```
make zvb
```

### If you wish to generate HDL sources without running Vivado, you can use:

<!-- name="generate" -->
```
make generate
```
