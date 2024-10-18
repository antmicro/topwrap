(installation)=

# Installing Topwrap

1. Install the required system packages:

    Debian:
    ```bash
    apt install -y git g++ make python3 python3-pip yosys npm
    ```

    Arch:
    ```bash
    pacman -Syu git gcc make python3 python-pip yosys npm
    ```

    Fedora:
    ```bash
    dnf install git g++ make python3 python3-pip python3-devel yosys npm
    ```

2. Install the Topwrap package (It is highly recommended to run this step in a Python virtual environment, such as [venv](https://docs.python.org/3/library/venv.html)):

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install .
    ```
    
Alternatively, to install using the pip package manager, use:

    ```bash
    pip install https://github.com/antmicro/topwrap/releases/download/latest/topwrap-0.1.0.tar.gz
    ```
    
:::{note}
To use the `topwrap parse` command, install optional dependencies:
```bash
apt install -y antlr4 libantlr4-runtime-dev
pip install ".[topwrap-parse]"
```
On Arch-based distributions, a symlink to the antlr4 runtime library needs to created and an environment variable set:
```bash
pacman -Syu antlr4 antlr4-runtime
ln -s /usr/share/java/antlr-complete.jar antlr4-complete.jar
ANTLR_COMPLETE_PATH=`pwd` pip install ".[topwrap-parse]"
```

On Fedora-based distributions, symlinks need to be made inside the `/usr/share/java` directory itself:
```bash
dnf install antlr4 antlr4-cpp-runtime-devel
sudo ln -s /usr/share/java/stringtemplate4/ST4.jar /usr/share/java/stringtemplate4.jar
sudo ln -s /usr/share/java/antlr4/antlr4.jar /usr/share/java/antlr4.jar
sudo ln -s /usr/share/java/antlr4/antlr4-runtime.jar /usr/share/java/antlr4-runtime.jar
sudo ln -s /usr/share/java/treelayout/org.abego.treelayout.core.jar /usr/share/java/treelayout.jar
pip install ".[topwrap-parse]"
```

[comment]: is there a way to clean up these instructions so they're not so lengthy? 

:::

If you want to contribute to the project, check the [Developer's setup guide](developers_guide/setup.md) for more information.
