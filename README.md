# FPGA Topwrap

Copyright (c) 2021-2023 [Antmicro](https://antmicro.com)

This is a Python package for generating HDL wrappers and top modules for your HDL source, resulting in a fully synthesizable design.

### Install package requirements:

With your package manager you need to install:
* python3 and pip.
* ANTLR4 for parsing Verilog files with `hdlConvertor`.
* Yosys, which is used to extract information about IP cores' interfaces from Verilog.

```
$(command -v sudo) apt-get install -y git python3 python3-pip antlr4 libantlr4-runtime-dev yosys
pip3 install -r requirements.txt
```

### Build and install the Topwrap package:

```
python3 setup.py build
python3 setup.py install
```

For more information about Topwrap, see the [Documentation](https://antmicro.github.io/fpga-topwrap/).
