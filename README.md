# Topwrap

Copyright (c) 2021-2024 [Antmicro](https://antmicro.com)

Topwrap leverages modularity to enable the reuse of design blocks across
different projects, facilitating the transition to automated logic design.
It provides a standardized approach for organizing blocks into various
configurations, making top-level designs easier to parse and process
automatically.

As a tool, Topwrap makes it straightforward to build complex and synthesizable
designs by generating a design file. The combination of GUI and CLI-based
configuration options provides for fine-tuning possibilities. Packaging multiple
files is accomplished by including them in a custom user repository, and an
internal API enables repository creation using Python.

![GUI example](docs/source/img/soc-diagram-anim.gif)

## Installation

Follow these steps to install the required dependencies:

```bash
curl -fO https://raw.githubusercontent.com/antmicro/topwrap/refs/heads/main/install-deps.sh
chmod +x ./install-deps.sh
sudo ./install-deps.sh
```

Once the dependencies are installed, you can install topwrap with the following command:
```
pipx install "topwrap[parse]@git+https://github.com/antmicro/topwrap"
```

More detailed instructions, are available in the
[installation guide](https://antmicro.github.io/topwrap/getting_started.html#installation).

## Functionality

Topwrap offers functionality in three main areas via the following commands:

- `topwrap parse` - automatically parses HDL modules and groups ports into
  interfaces to enable connecting them more conveniently in the design.
- `topwrap build` - generates the top level based on a design description file.
- `topwrap kpm_client` - spawns a [GUI](https://github.com/antmicro/kenning-pipeline-manager) for creating designs.

## Resources

Additional information, example projects, tutorials and the developer's guide
can be found in the [project documentation](https://antmicro.github.io/topwrap/introduction.html).
