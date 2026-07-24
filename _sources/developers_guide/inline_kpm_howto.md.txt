# Using KPM iframes inside docs

It is possible to use the `pipeline_manager` Sphinx directive to embed KPM directly inside a doc.

## Usage

````
```{pipeline_manager}
:spec: <KPM specification .json file URI>
:graph: <KPM dataflow .json file URI>
:preview: <a Boolean value specifying whether this KPM should be started in preview mode>
:height: <a string CSS height property that sets the `height` of the iframe>
:alt: <a custom alternative text used in the PDF documentation instead of the default one>
```
````

`URI` represents either a local file from sources that are copied into the build directory, or a remote resource.

All parameters in this directive are optional.

## Tests

### Use local files

```{pipeline_manager}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:graph: ../../../tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:height: 80vh
```
### Open in preview mode

```{pipeline_manager}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:graph: ../../../tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:preview: true
```

### Use a custom alt text

:::{note}
The alternative text is visible instead of the iframe in the PDF version of this documentation.
:::

```{pipeline_manager}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:graph: ../../../tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:alt: This diagram showcases the block design of the "hierarchy" example
```
