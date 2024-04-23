(future-enhancements)=

# Future enhancements

(hierarchical-block-designs)=
## Support for hierarchical block design in Pipeline Manager

Currently topwrap supports creating hierarchical designs only by manually writing the hierarchy in the design description YAML.
Supporting such feature in the Pipeline Manager via its subgraphs would be a huge improvement in terms of organizing complex designs.

(bus-management)=
## Bus management

Another goal we'd like to achieve is to enable users to create full-featured designs with processors by providing proper support for bus management.
This should include features such as:

* ability to specify the address of a peripheral device on the bus
* support for the most popular buses or the ones that we use (AXI, wishbone, Tile-link)

This will require writing or creating bus arbiters (round-robin, crossbar) and providing a mechanism for connecting master(s) and slave(s) together.
As a result, the user should be able to create complex SoC with Topwrap.

Currently only experimental support for Wishbone with a round-robin arbiter {ref}`is available <interconnect-generation>`.

(improve-recreating-design)=
## Improve the process of recreating a design from a YAML file

One of the main features that are supported by Topwrap and Pipeline Manager is exporting and importing user-created design to or from a design description YAML. However, during these conversions, information about the positions of user-added nodes is not preserved. This is cumbersome in the case of complicated designs since the imported nodes cannot be placed in the optimal positions.

Therefore, one of our objectives is to provide a convenient way of creating and restoring user-created designs in Pipeline Manager, so that the user doesn't have to worry about node positions when importing a design to Pipeline Manager.

(systemverilog-parsing)=
## Support for parsing SystemVerilog sources

Information about IP cores is stored in {ref}`IP core description YAMLs <ip-description>`. These files can be generated automatically from HDL source files - currently Verilog and VHDL are supported. Our goal is to provide the possibility of generating such YAMLs from SystemVerilog too.

(pm-hdl-parsing)=
## Provide a way to parse HDL sources from the Pipeline Manager level

Another issue related to HDL parsing is that the user has to manually parse HDL sources to obtain the IP core description YAMLs. Then the files need to be provided as command-line parameters when launching the Topwrap Pipeline Manager client application. Therefore, we aim to provide a way of parsing HDL files and including them in the editor directly from the Pipeline Manager level.

(toplevel-vhdl)=
## Ability to produce top-level wrappers in VHDL

Topwrap now uses Amaranth to generate top-level design in Verilog. We would also like to add the ability to produce such designs in VHDL.

(core-library)=
## Library of open-source cores

Currently user has to supply all of the cores used in the design manually or semi-manually (e.g. through FuseSoC).
A repository of open-source cores that could be easily reused in topwrap would improve convenience and allow quickly putting together a design from premade hardware blocks.

(tools-integration)=
## Integrating with other tools

Topwrap can build the design but testing and synthesis rely on the user - they have to automate this process themselves (e.g. with makefiles).
Ideally the user should be able to write scripts that integrate tools for synthesis, simulation and co-simulation (e.g. with Renode) with topwrap.
Some would come pre-packaged with topwrap (e.g. simulation with verilator, synthesis with vivado).
It should also be possible to invoke these from the Pipeline Manager GUI by using its ability to add custom buttons and integrated terminal.
