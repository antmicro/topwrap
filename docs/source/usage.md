# Using Topwrap

(GUI)=
## GUI

Topwrap can make use of a [GUI](https://github.com/antmicro/kenning-pipeline-manager) to visualize the process of creating block designs.

(kenning-pipeline-manager)=

### Running Topwrap with the GUI

1. Build and run the GUI server

    In order to start creating block designs in the GUI, you need to first build and run the server application (the process of building and installation of the GUI is described in detail in its [documentation](https://antmicro.github.io/kenning-pipeline-manager/project-readme.html#building-and-running)):

    ```
    python -m topwrap kpm_build_server
    python -m topwrap kpm_run_server
    ```

    After executing the above commands, the GUI server is waiting for an external application (i.e. Topwrap) to connect on `127.0.0.1:9000` and you can connect to the Web GUI frontend in your browser at `http://127.0.0.1:5000`.
    
[comment:] Is there a way to simplify this, so it doesn't require the user to visit a different project (and install it)? 

2. Establish connection with Topwrap

    Once the GUI server is running, you can now launch Topwrap's client application in order to connect to the server. You need to specify:
    * IP address (`127.0.0.1` is set by default)
    * listening port (`9000` is set by default)
    * YAMLs describing IP cores, that will be used in the block design
    * design to load initially (`None` is set by default)

    An example command to run the Topwrap client can look like this:
    ```
    python -m topwrap kpm_client -h 127.0.0.1 -p 9000 \
        topwrap/ips/axi/axi_axil_adapter.yaml \
        examples/pwm/ipcores/{litex_pwm.yml,ps7.yaml} -d examples/pwm/project.yml
    ```

[comment]: should we mention here how to change the IP address and port?

3. Create a block design in the GUI

    Upon successful connection to the server, Topwrap will generate and send to the server a specification describing the structure of previously selected IP cores. If the `-d` option was used, a design will be shown in the GUI. From there you can create or modify designs by:
    * adding IP core instances to the block design. Each node in the GUI has `delete` and `rename` options, which makes it possible to remove the selected node and change its name respectively. This means that you can create multiple instances of the same IP core.
    * adjusting IP cores' parameters values. Each node may have input boxes in which you can enter parameter values (default parameter values are added while adding an IP core to the block design):
    ```{image} img/node_parameters.png
    ```
    * connecting IP cores' ports and interfaces. Only connections between ports or interfaces of matching types are allowed. This is automatically checked by the GUI, as the types of nodes' ports and interfaces are contained in the loaded specification, so the GUI will prevent you from connecting non-matching interfaces (e.g. *AXI4* with *AXI4Lite* or a port with an interface). A green line will be displayed if a connection is possible to create, or a red line elsewhere:
    ```{image} img/invalid_connection.png
    ```
    * specifying external ports or interfaces in the top module. This can be done by adding `External Input`, `External Output` or `External Inout` metanodes and creating connections between them and the chosen ports or interfaces. Note that you should adjust the name of the external port or interface in the textbox inside the selected metanode. In the example below, the output port `pwm` of `litex_pwm_top` IP core is external to the generated top module and the external port name will be set to `ext_pwm`:
    ```{image} img/external_port.png
    ```
    You don't always have to create a new block design by hand - you can use a {ref}`design import <import-design>` feature to load an existing block design from a description in Topwrap's YAML format.

    An example block design in Pipeline Manager for the PWM project may look like this:

    ```{image} img/pwm_design.png
    ```

### Pipeline Manager features

While creating a custom block design, you can make use of the following Pipeline Manager features:
* Export (save) designs to a file
* Import (load) designs from a file
* Validating designs
* Building design

(export-design)=

#### Export design to a YAML description file

The created block design can be saved to a {ref}`design description file <design-description>` in the YAML format, using Pipeline Manager's `Save file` option.
The target location on the filesystem can then be chosen in the filesystem dialog window.

(import-design)=

#### Import designs from YAML description files

Topwrap also supports conversion in the opposite way - block designs in Pipeline Manager can be generated from a YAML design description file using the `Load file` feature.

(validate-design)=

#### Validating designs

Pipeline Manager is capable of performing some basic checks at runtime such as interface type checking while creating a connection. More complex tests can be run by using Pipeline Manager's `Validate` option. Topwrap will then respond with a validity confirmation or an error message. 

The rules you need to follow in order to create a valid block design are:
* multiple IP cores with the same name are not allowed (except from external metanodes).
* parameters values can be integers of different bases (e.g. `0x28`, `40` or `0b101000`) or arithmetic expressions, that are later evaluated using [numexpr.evaluate()](https://numexpr.readthedocs.io/en/latest/api.html#numexpr.evaluate) function (e.g. `(AXI_DATA_WIDTH+1)/4` is a valid parameter value assuming that a parameter named `AXI_DATA_WIDTH` exists in the same IP core). You can also write a parameter value in a Verilog format (e.g. `8'b00011111` or `8'h1F`) - in such cases it will be interpreted as a fixed-width bit vector.
* a single port or interface cannot be external and connected to another IP core at the same time.
* connections between two external metanodes are not allowed.
* all the created external output or inout ports must have unique names. Only multiple input ports of IP cores can be driven be the same external signal.

Topwrap can also generate warnings if:
* some ports or interfaces remain unconnected.
* multiple ports are connected to an `External Input` metanode with an empty `External Name` property.
* `inout` ports of two modules are connected together (all `inout` ports are required to be directly connected to `External Inout` metanodes)

If validation of a block design returns a warning, it means that the block design can be successfully built, but it is recommended to follow the suggestions and resolve the highlight issue(s).

(build-design)=

#### Building designs

Once the design has been created and validated, you can build the design by using `Run` button. If the design does not contain any errors, a top module is created in the directory where `topwrap kpm_client` was run, in a similar manner as using Topwrap's `topwrap build` command.

## CLI

Topwrap has a couple CLI only functions that expand on the functionality offered by the GUI.

(generating-ip-yamls)=
### Generating IP core description YAMLs

You can use Topwrap to generate IP core description YAMLs from HDL sources to use them in your `project.yml`.
To learn more about project and core YAMLs, check the {ref}`design description <design-description>` and {ref}`ip description <ip-description>`

```
python -m topwrap parse HDL_FILES
```

In HDL source files, ports that belong to the same interface (e.g. wishbone or AXI),
often have a common prefix, which corresponds to the interface name. If the naming
convention is followed in the HDL sources, Topwrap can also divide ports into user-specified
interfaces, or automatically deduce interface names when generating YAML files:

```
python -m topwrap parse --iface wishbone --iface s_axi HDL_FILES

python -m topwrap parse --iface-deduce HDL_FILES
```

For help, use:

```
python -m topwrap [build|kpm_client|parse] --help
```

(building-design)=

### Building design

Topwrap can build a synthesizable design from source files described in a design file. To do this, run:

```
python -m topwrap build --design project.yml
```

Where `project.yml` should be your file with a description of the top module.

You can specify a directory to be scanned for additional sources:

```
python -m topwrap build --sources src --design project.yml
```

To implement the design for a specific FPGA chip, provide the part name:

```
python -m topwrap build --sources src --design project.yml --part 'xc7z020clg400-3'
```
