# Topwrap

Copyright (c) 2021-2024 [Antmicro](https://antmicro.com)

This is a Python package for generating HDL wrappers and top modules for your HDL source, resulting in a fully synthesizable design.

### Install package requirements:

With your package manager you need to install:
* python3 and pip.
* ANTLR4 for parsing Verilog files with `hdlConvertor`.
* Yosys, which is used to extract information about IP cores' interfaces from Verilog.

```
$(command -v sudo) apt-get install -y git g++ make python3 python3-pip antlr4 libantlr4-runtime-dev yosys
```

### Install the Topwrap package:

```
pip3 install .
```

For more information about Topwrap, see the [Documentation](https://antmicro.github.io/topwrap/).
