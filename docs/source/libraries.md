# Libraries

A library is a directory of [CAPI2](https://fusesoc.readthedocs.io/en/stable/ref/capi2.html) `.core` files that describe IP cores and interface definitions. Topwrap resolves them with FuseSoC, so a library can be a plain local directory or a git repository.

A library is not laid out by convention: each `.core` file states which of its files Topwrap should read, and what they are.

## Registering a library

```bash
topwrap library add my_cores ./path/to/cores
topwrap library add remote_cores https://github.com/example/cores.git
```

The name is what the library is referred to by; the URI is a local directory or a git URL. A git URL may carry a `@<ref>` suffix to pin a branch, tag, or commit:

```bash
topwrap library add pinned https://github.com/example/cores.git@v1.2.0
```

Registering writes the entry to the `libraries:` section of `topwrap.yaml` in the current directory, and checks a git library out into a project-local `.fusesoc-cores/` directory. Because the checkout is project-local, two projects never contend over the same clone.

To fetch the latest upstream state of the registered git libraries:

```bash
topwrap library update            # all of them
topwrap library update my_cores   # or just one
```

## Inspecting libraries

```bash
topwrap library list              # registered libraries and their checkout state
topwrap library list modules      # IP modules each one provides
topwrap library list interfaces   # interface definitions each one provides
topwrap library list all          # both
```

Each of the listing commands accepts `--design <file>`, which also takes into account the libraries declared in that design's `config:` section.

## Describing library contents

A `.core` file marks each file it contributes with a `file_type`, which is what tells Topwrap how to read it:

- `topwrapModule` — an [IP description](description_files.md#ip-description-files)
- `topwrapInterface` — an [interface definition](description_files.md#interface-definition-files)

```yaml
CAPI=2:

name : example.com:my-cores:fifo

filesets:
  topwrap:
    files:
        - module.yaml : { file_type : topwrapModule }
```

A single `.core` may contribute any number of modules and interfaces. Files without one of these types are ignored by Topwrap.

The identifier a module or interface is known by comes from the `id:` field of the YAML file itself, not from the `name:` of the `.core` that lists it. Keep the two in agreement, or the core will advertise a name that nothing resolves by.

## Referencing a library module

In a design, `core:` takes the VLNV of a module from any registered library:

```yaml
ips:
  adapter:
    core: vendor:libdefault:axi_axil_adapter:0.1
```

The reference may be partial, and is matched right-aligned onto `vendor:library:name`, so all of these select the same module when unambiguous:

```yaml
core: axi_axil_adapter                 # just the name
core: libdefault:axi_axil_adapter      # library and name
core: :libdefault:axi_axil_adapter     # an empty field is a wildcard
```

Spelling out all four fields also constrains the version. A reference that matches nothing, or more than one module, is an error that names the candidates.

`core:` and `file:` are mutually exclusive — each IP instance uses exactly one.

## Declaring libraries in a design

A design can register libraries for its own parse, without touching `topwrap.yaml`:

```yaml
config:
  libraries:
    my_cores: ./cores
```

Relative paths are resolved against the design file. This is how a design stays self-contained for anyone who checks it out.
