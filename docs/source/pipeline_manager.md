(kenning-pipeline-manager)=

# Kenning Pipeline Manager

Topwrap can make use of [Kenning Pipeline Manager](https://github.com/antmicro/kenning-pipeline-manager) to visualize the process of creating block design.

## Run Topwrap with Pipeline Manager

1. Build and run Pipeline Manager server

    In order to start creating block design in Pipeline Manager, you need to first build and run a server application - here is a brief instruction on how to achieve this (the process of building and installation of Pipeline Manager is described in detail in its [documentation](https://antmicro.github.io/kenning-pipeline-manager/project-readme.html#building-and-running)):

    ```
    git clone https://github.com/antmicro/kenning-pipeline-manager.git
    cd kenning-pipeline-manager
    pip install -r requirements.txt
    ./build server-app
    ./run
    ```

    After executing the above-mentioned commands, the Pipeline Manager server is running on `http://127.0.0.1:5000` and waiting for an external application (i.e. Topwrap) to connect on `http://127.0.0.1:9000`.

2. Establish connection with Topwrap

    Once the Pipeline Manager server is running, you can now launch Topwrap's client application and connect it to the server. You need to specify IP address and listening port to which the connection will be established and choose IP core description yamls, that will be used in the block design:

    ```
    python -m fpga_topwrap kpm_client -h 127.0.0.1 -p 9000 \
        fpga_topwrap/ips/axi/axi_axil_adapter.yaml \
        examples/pwm/ipcores/{litex_pwm.yml,ps7.yaml}
    ```

3. Create block design in Pipeline Manager

    Upon successful connection to a Pipeline Manager server, Topwrap will generate and send to it a specification describing the structure of previously selected IP cores. After that, you are free to create a custom block design by linking ports and interfaces of the selected IP cores and changing their parameters:

    ```{image} img/pwm_design.png
    ```

    There are several rules, that need to be followed while creating a block desing:
    * only connections between ports or interfaces of matching types are allowed. This is however automatically checked by the Pipeline Manager, as the types of nodes' inputs and outputs are contained in the loaded specification, so Pipeline Manager will prevent you from connecting non-matching interfaces (e.g. *AXI4* with *AXI4Lite*).
    * parameters values can be integers of different bases (e.g. `0x28`, `40` or `0b101000`) or arithmetic expressions, that are later evaluated using [numexpr.evaluate()](https://numexpr.readthedocs.io/en/latest/api.html#numexpr.evaluate) function (e.g. `(AXI_DATA_WIDTH+1)/4` is a valid parameter value assuming that a parameter named `AXI_DATA_WIDTH` exists in the same IP core). You can also write a parameter value in a Verilog format (e.g. `8'b00011111` or `8'h1F`) - in such case it will be interpreted as a fixed-width bit vector. In order to check the validity of provided parameters values, use a {ref}`design validation <validate-design>` feature.

    Note, that you don't always have to create a new block design by hand - you can use a {ref}`design import <import-design>` feature to load an existing block design from a description in Topwrap's yaml format.

## Pipeline Manager features

While creating a custom block design, you can make use of the following Pipeline Manager's features:
* export (save) design to a file
* import (load) design from a file
* validate design
* build design

(export-design)=

### Export design to yaml description file

Created block design can be saved to a {ref}`design description file <design-description>` in yaml format, using Pipeline Manager's `Save file` option. The design description file name will be generated automatically based on current timestamp.

(import-design)=

### Import design from yaml description file

Topwrap also supports conversion in the opposite way - block design in Pipeline Manager can be generated from a yaml design description file using `Load file` feature.

(validate-design)=

### Design validation

In order to check whether a created design is valid, you can use Pipeline Manager's `Validate` option. Topwrap will then perform some checks on the design and respond with a validity confirmation or error messages (e.g. invalid parameters values or duplicate block names).

(build-design)=

### Building design

Once the design has been created and tested for validity, you can build design using `Run` feature. If the design does not contain any errors, this will result in creating a top module, similarly when using Topwrap's `fpga_topwrap build` command.
