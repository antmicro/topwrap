# Topwrap SoC example setup

Copyright (c) 2024 [Antmicro](https://antmicro.com)

This is an example on how to use [Topwrap](https://github.com/antmicro/topwrap) to build a synthesizable SoC design.
The SoC contains a VexRiscv core, data and instruction memory, UART and interconnect that ties all components together.

## Install required dependencies

```
sudo apt install git make g++ ninja-build gcc-riscv64-unknown-elf bsdextrautils
```

To run the simulation you also need:
- verilator

To create and load bitstream you also need:
- vivado (preferably version 2020.2)
- openFPGALoader ([this branch](https://github.com/antmicro/openFPGALoader/tree/antmicro-ddr-tester-boards))

## Generate HDL sources

<!-- name="generate" -->
```
make generate
```

## Build and run simulation

```
make sim
```

Expected waveform generated by the simulation is shown in `expected-waveform.svg`.

## Generate bitstream

```
make bitstream
```
