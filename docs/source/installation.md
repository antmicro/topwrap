(installation)=
# Installing Topwrap

## 1. Install the required system packages

:::{warning}
The script below requires root privileges because it directly interfaces with your package manager and filesystem.

It's dangerous to run scripts and executables as root without verifying their contents beforehand!
Please make sure to do that before executing the script below.
:::

```bash
curl -fO https://raw.githubusercontent.com/antmicro/topwrap/refs/heads/main/install-deps.sh
chmod +x ./install-deps.sh
sudo ./install-deps.sh
```

## 2. Install the Topwrap package

**Recommended**: Use [pipx](https://pipx.pypa.io/stable/) to directly install Topwrap as a user package:

```bash
pipx install "topwrap[topwrap-parse]@git+https://github.com/antmicro/topwrap"
```

If you can't use pipx, you can use regular pip instead.
(It may be necessary to do it in a Python virtual environment, such as [venv](https://docs.python.org/3/library/venv.html)):

```bash
python3 -m venv venv
source venv/bin/activate
pip install "topwrap[topwrap-parse]@git+https://github.com/antmicro/topwrap"
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
