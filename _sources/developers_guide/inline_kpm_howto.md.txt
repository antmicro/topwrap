# Using KPM iframes inside docs

It is possible to use the `kpm_iframe` Sphinx directive to embed KPM directly inside a doc.

## Usage

````
```{kpm_iframe}
:spec: <KPM specification .json file URI>
:dataflow: <KPM dataflow .json file URI>
:preview: <a boolean value specifying whether this KPM should be started in preview mode>
:height: <a string css height property that sets the `height` of iframe>
:alt: <a custom alternative text used in the PDF documentation instead of the default one>
```
````

`URI` can represent either a local file from sources that gets copied into the build directory, or a remote resource.

All parameters of this directive are optional.


## Tests

### Use remote specification

:::{note}
The graph below is supposed to be empty.
It doesn't load a dataflow, only a specification that provides IP-cores to the Nodes browser on the sidebar.
:::

```{kpm_iframe}
:spec: https://raw.githubusercontent.com/antmicro/topwrap/main/tests/data/data_kpm/examples/hdmi/specification_hdmi.json
```

### Use local files

```{kpm_iframe}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:height: 80vh
```

### Open in preview mode

```{kpm_iframe}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:preview: true
```

### Use custom alt text

:::{note}
The alternative text is visible instead of the iframe in the PDF version of this documentation.
:::

```{kpm_iframe}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:dataflow: https://raw.githubusercontent.com/antmicro/topwrap/refs/heads/main/tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:alt: This diagram showcases the block design of the "hierarchy" example
```
