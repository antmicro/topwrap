(installation)=

# Installation

1. Install required system packages:

    Debian:
    ```bash
    apt install -y git g++ make python3 python3-pip antlr4 libantlr4-runtime-dev yosys npm
    ```

    Arch:
    ```bash
    pacman -Syu git gcc make python3 python-pip antlr4 antlr4-runtime yosys npm
    ```

    Fedora:
    ```bash
    dnf install git g++ make python3 python3-pip python3-devel antlr4 antlr4-cpp-runtime-devel yosys npm
    ```

2. Install the Topwrap package (It is highly recommended to run this step in a Python virtual environment, e.g. [venv](https://docs.python.org/3/library/venv.html)):

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install .
    ```

:::{note}
To use `topwrap parse` command you also need to install optional dependencies:
```bash
pip install ".[topwrap-parse]"
```
On Arch-based distributions a symlink to antlr4 runtime library needs to created and an environment variable set:
```bash
ln -s /usr/share/java/antlr-complete.jar antlr4-complete.jar
ANTLR_COMPLETE_PATH=`pwd` pip install ".[topwrap-parse]"
```
On Fedora-based distributions symlinks need to be made inside `/usr/share/java` directory itself:
```bash
sudo ln -s /usr/share/java/stringtemplate4/ST4.jar /usr/share/java/stringtemplate4.jar
sudo ln -s /usr/share/java/antlr4/antlr4.jar /usr/share/java/antlr4.jar
sudo ln -s /usr/share/java/antlr4/antlr4-runtime.jar /usr/share/java/antlr4-runtime.jar
sudo ln -s /usr/share/java/treelayout/org.abego.treelayout.core.jar /usr/share/java/treelayout.jar
pip install ".[topwrap-parse]"
```
:::

If you want to contribute to the project please see the [Developer's setup guide](developers_guide/setup.md).
