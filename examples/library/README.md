Copyright (c) 2026 [Antmicro](https://antmicro.com)

# Example of a project using a FuseSoC library

This example demonstrates the `libraries:` mechanism,
successor to [user repositories](../user_repository). A library is a
directory (local, here, or a git repository) of
[CAPI2](https://fusesoc.readthedocs.io/en/stable/ref/capi2.html) `.core`
files, each marking which of its files Topwrap should treat as an IP core
or interface description, and which are ordinary HDL sources for a real
build:

```yaml
CAPI=2:

name : example.com:demo:producer

filesets:
  topwrap:
    files:
        - module.yaml : { file_type : topwrapModule }
  rtl:
    files:
        - producer.sv : { file_type : systemVerilogSource }

targets:
  default:
    filesets: [rtl]
```

`cores/producer/module.yaml` and `producer.core` started out as the output
of `topwrap package`, which parses HDL sources into a Topwrap IP
description and, with `--lib`, a matching `.core` file - `+incdir+`,
`+define+`, and `-f <filelist>` work the same way they do for other EDA
tools. `p_data`/`p_valid` are just plain ports as far as the SystemVerilog
source goes, so recovering the `demo_stream` interface grouping below needs
`--inference` matched against a registered library, plus `--grouping-hint`
to name the result (inference can tell the ports belong together, not what
a human would call the group):

```bash
topwrap library add demo_cores ./cores   # writes topwrap.yaml, see below
topwrap package cores/producer/producer.sv --vlnv example.com:demo:producer:0.1 \
  --inference --grouping-hint p=stream_out --lib -o cores/producer/module.yaml
```

or, to recreate both cores at once:

```bash
make cores
```

The library also provides a custom interface, `demo_stream`, the same way
a module is provided — a `.core` file marking a YAML description as
`topwrapInterface` (see `cores/stream_if/`). `producer` drives it as a
manager, `consumer` receives it as a subordinate; the design connects them
under `connections.interfaces` rather than wiring `data`/`valid` up as
plain ports.

The design registers the library itself, in its own `config:` section —
no `topwrap.yaml` needed:

```yaml
config:
  libraries:
    demo_cores: ./cores
```

and refers to its modules with `core:` instead of `file:`, either by a
full `vendor:library:name:version` identifier or, when unambiguous, just
the name:

```yaml
ips:
  producer:
    core: example.com:demo:producer:0.1
  consumer:
    core: consumer
```

A library can just as well be registered in `topwrap.yaml` instead,
which is the better fit once more than one design in a project shares it
— see the [libraries](https://antmicro.github.io/topwrap/libraries.html)
documentation.

## Usage

```bash
topwrap library list all --design project.yaml
topwrap generate project.yaml --specification --diagram
make gui   # or: topwrap gui -d project.yaml
```

A real library would typically live in its own git repository;
registering one in `topwrap.yaml` is a matter of

```bash
topwrap library add my_lib https://example.com/my-cores.git
```

which clones it into a project-local `.fusesoc-cores/` directory.
