# FPGA Topwrap example: inout

Copyright (c) 2023 [Antmicro](https://antmicro.com)

This examples presents usage of inout ports in a small design, which can be reused to quickly test features.

## Generate bitstream for Zynq:

<!-- name="build" -->
```
make
```

## Generate HDL sources without implementation:

<!-- name="generate" -->
```
make generate
```

## Contents of the design

Design consists of 3 modules: input buffer `ibuf`, output buffer `obuf`, bidirectional buffer `iobuf`. Their operation can be described as:
* input buffer is a synchronous D-type flip flop with an asynchronous reset
* output buffer is a synchronous D-type flip flop with an asynchronous reset and an `output enable`, which sets output to high impedance state (Hi-Z)
* inout buffer instantiates 1 input and 1 output buffer. Input of the `ibuf` and output of the `obuf` are connected with an inout wire (port).
