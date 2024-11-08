(future-enhancements)=
# Future planned enhancements in Topwrap

(future-core-library)=
## Library of open-source cores

Currently, users have to manually or semi-manually (e.g. through FuseSoC) supply all of the cores used in the design. In future, a repository of open-source cores that can be easily reused will be provided, allowing users to quickly put together designs from premade hardware blocks.

(future-hierarchical-block-designs)=
## Support for hierarchical block designs in Topwrap's GUI

Currently Topwrap supports creating hierarchical designs by manually writing the hierarchy in the design description YAML, while in future, this feature will be additionally supported in the GUI for visually organizing complex designs.

(future-systemverilog-parsing)=
## Support for parsing SystemVerilog sources

Information about IP cores is stored in {ref}`IP core description YAMLs <design-description-ip-description>`. These files can be generated automatically from HDL source files - currently Verilog and VHDL are supported. In a future release, Topwrap will also provide the possibility of generating YAMLs from SystemVerilog.

(possible-improvements)=
# Other possible improvements

(possible-improvements-toplevel-vhdl)=
## Ability to produce top-level wrappers in VHDL

Topwrap currently uses Amaranth to generate top-level designs in Verilog. We could also add the ability to produce such designs in VHDL.

(possible-improvements-bus-management)=
## Bus management

Another feature that we could introduce is allowing users to create full-featured designs with processors by providing proper support for bus management.
This should include features such as:

* ability to specify the address of a peripheral device on the bus
* support for the most popular buses (AXI, TileLink, Wishbone)

This will require writing or creating bus arbiters (round-robin, crossbar) and providing a mechanism for connecting manager(s) and subordinate(s) together. As a result, the user would be able to create complex SoCs directly in Topwrap. 

Currently, only experimental support for Wishbone with a round-robin arbiter {ref}`is available <interconnect-generation>`.

(possible-improvements-recreating-design)=
## Improve the process of recreating a design from a YAML file

One of the main features that are supported by Topwrap and the GUI is exporting and importing user-created designs to or from a design description YAML. However, during these conversions, information about the position of user-added nodes is not preserved. This is cumbersome in the case of complicated designs since the imported nodes are not retained in the most optimal positions.

Therefore, one of our objectives is to provide a convenient way of creating and restoring user-created designs in the GUI, so that the node positions are retained.

(possible-improvements-tools-integration)=
## Deeper integration with other tools

Topwrap can build designs, but testing and synthesis rely on the user - they have to automate this process themselves (e.g. with makefiles). To improve the usability of Topwrap, a potential area of improvement is to integrate tools for synthesis, simulation and co-simulation (e.g. [Renode](https://www.renode.io) with Topwrap, accessible through scripts. Some could be pre-packaged with Topwrap (e.g. simulation with Verilator, synthesis with Vivado).
It should also be possible to invoke these from the GUI by adding custom buttons or through the integrated terminal.

(possible-improvements-gui-hdl-parsing)=
## Provide a way to parse HDL sources from the GUI level

Another issue related to HDL parsing is that the user has to manually parse HDL sources to obtain the IP core description YAMLs. These files then need to be provided as command-line parameters when launching the Topwrap GUI client application. Therefore, we aim to provide a way of parsing HDL files so that they can be included in the editor, directly from the GUI.