# Installing Topwrap

## 1. Install required system packages

:::{caution}
Topwrap has been tested on Debian Bullseye and Bookworm, both of which include ANTLR4 version 4.7.2. \
This specific version is required for the proper operation of one of Topwrap's dependencies,  [hdlConvertor](https://github.com/Nic30/hdlConvertor). \
While other distributions may also be compatible, Bullseye and Bookworm reflect environments where functionality has been verified.
:::

On Debian and Debian-based distributions, follow these steps to install the required dependencies:

```bash
apt install -y python3 python3-pip yosys npm antlr4 libantlr4-runtime-dev pipx
```

## 2. Install the Topwrap user package

**Recommended**: Use [pipx](https://pipx.pypa.io/stable/) to directly install Topwrap as a user package:

```bash
pipx install "topwrap[parse]@git+https://github.com/antmicro/topwrap"
```

If you can't use pipx, you can use regular pip instead. It may be necessary to do it in a Python virtual environment, such as [venv](https://docs.python.org/3/library/venv.html):

```bash
python3 -m venv venv
source venv/bin/activate
pip install "topwrap[parse]@git+https://github.com/antmicro/topwrap"
```

## 3. Verify the installation

Make sure that Topwrap was installed correctly and is available in your shell:

```bash
topwrap --help
```

This should print out the help string with Topwrap subcommands listed out.

:::{seealso}
If you want to contribute to the project, check the [Developer's setup guide](developers_guide/setup.md) for more information.
:::
