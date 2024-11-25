# Introduction to Topwrap

![Topwrap logo](img/topwrap-logo--mono.png)

Topwrap leverages modularity to enable the reuse of design blocks across different projects, facilitating the transition to automated logic design. It provides a standardized approach for organizing blocks into various configurations, making top-level designs easier to parse and process automatically.

As a tool, Topwrap makes it [straightforward to build](getting_started.md) complex and [synthesizable designs](#examples) by generating a design file. The combination of [GUI and CLI-based](getting_started.md#generating-verilog-in-the-gui) configuration options provides for fine-tuning possibilities. Packaging multiple files is accomplished by including them in a [custom user repository](user_repositories.md), and an internal API enables repository creation using Python.

Topwrap uses [FuseSoC](fusesoc.md) to automate project generation and build processes.

![GUI example](img/soc-diagram-anim.gif)
