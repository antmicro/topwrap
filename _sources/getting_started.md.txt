(getting-started)=

# Getting started

## Installation

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

(example-usage)=

## Example usage

This section demonstrates the basic usage of Topwrap to generate IP wrappers and a top module.

1. Create {ref}`IP core description <ip-description>` file for every IP Core you want to use or let {ref}`topwrap parse <generating-ip-yamls>` handle this for you. This file describes the ports, parameters and interfaces of an IP core.

As an example, Verilog module such as:

```verilog
module ibuf (
    input  wire clk,
    input  wire rst,
    input  wire a,
    output reg z
);
    // ...
endmodule
```

Needs this corresponding description:

```yaml
signals:
  in:
    - clk
    - rst
    - a
  out:
    - z
```

2. Create a {ref}`design description <design-description>` file where you can specify all instances of IP cores and connections between them (`project.yaml` in this example)

- Create instances of IP cores:

```yaml
ips:
  vexriscv_instance:
    file: ipcores/gen_VexRiscv.yaml
    module: VexRiscv
  wb_ram_data_instance:
    file: ipcores/gen_mem.yaml
    module: mem
  wb_ram_instr_instance:
    file: ipcores/gen_mem.yaml
    module: mem

```

`file` and `module` are mandatory fields providing the IP description file and the name of the HDL module as it appears in the source.

- (Optional) Set parameters for IP core instances:

```yaml
parameters:
  wb_ram_data_instance:
    depth: 0x1000
    memfile: "top_sram.init"
  wb_ram_instr_instance:
    depth: 0xA000
    memfile: "bios.init"
```

- Connect desired ports of the IP cores:

```yaml
ports:
  wb_ram_data_instance:
    clk: [some_other_ip, clk_out]
    rst: [reset_core, reset0]
  wb_ram_instr_instance:
    clk: [some_other_ip, clk_out]
    rst: [reset_core, reset0]
  vexriscv_instance:
    softwareInterrupt: [some_other_ip, sw_interrupt]
    ...
```

Connections only need to be written once, i.e. if A connects to B, then only a connection A: B has to be specified (B: A is redundant).

- Connect desired interfaces of the IP cores:

```yaml
interfaces:
  vexriscv_instance:
    iBusWishbone: [wb_ram_instr_instance, mem_bus]
    dBusWishbone: [wb_ram_data_instance, mem_bus]
```

- Specify external ports or interfaces of the top module and connect them with chosen IP cores' ports or interfaces:

```yaml
ports:
  vexriscv_instance:
    timerInterrupt: ext_timer_interrupt

...

external:
  ports:
    out:
      - ext_timer_interrupt
  interfaces:
    ...
```

3. Create a Core file template for FuseSoC, or use a default one bundled with Topwrap.

You may want to modify the file to add dependencies, source files, or change the target board.
The file should be named `core.yaml.j2`. You can find an example template in `examples/hdmi` directory of the project.
If you don't create any template a default template bundled with Topwrap will be used (stored in `templates` directory).

4. Place any additional source files in a directory (`sources` in this example).

5. Run Topwrap:

   ```
   python -m topwrap build --design project.yaml --sources sources
   ```

### Example PWM design

There's an example setup in `examples/pwm`.

In order to generate the top module, run:

```
make generate
```

In order to generate bitstream, add Vivado to your path and run:

```
make
```

The FPGA design utilizes an AXI-mapped PWM IP Core.
You can access its registers starting from address `0x4000000` (that's the base address of `AXI_GP0` on ZYNQ).
Each IP Core used in the project is declared in `ips` section in `project.yml` file.
`ports` section allows to connect individual ports of IP Cores, and `interfaces` is used analogously for connecting whole interfaces.
Finally, you can specify which ports will be used as external I/O in `external` section.

To connect the I/O signals to specific FPGA pins, you need proper mappings in a constraints file. See `zynq.xdc` used in the setup and modify it accordingly.

```{image} img/pwm.png
```

### Example HDMI design

There's an example setup stored in `examples/hdmi`.

You can generate bitstream for desired target:

> - Snickerdoodle Black:
>
>   ```
>   make snickerdoodle
>   ```
>
> - Zynq Video Board:
>
>   ```
>   make zvb
>   ```

If you wish to generate HDL sources without running Vivado, you can use:

```
make generate
```

You can find more information in README of the example setup.
