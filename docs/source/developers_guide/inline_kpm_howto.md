(dev-guide-kpm-iframes)=
# Using KPM iframes inside docs

It is possible to use the `kpm_iframe` Sphinx directive to embed KPM directly inside a doc.

(dev-guide-kpm-iframes-usage)=
## Usage

````
```{kpm_iframe}
:spec: <KPM specification .json file URI>
:dataflow: <KPM dataflow .json file URI>
:preview: <a Boolean value specifying whether this KPM should be started in preview mode>
:height: <a string CSS height property that sets the `height` of the iframe>
:alt: <a custom alternative text used in the PDF documentation instead of the default one>
```
````

`URI` represents either a local file from sources that are copied into the build directory, or a remote resource.

All parameters in this directive are optional.

(dev-guide-kpm-iframes-tests)=
## Tests

(dev-guide-kpm-iframes-usage-tests-spec)=
### Use remote specification

:::{note}
The graph below is supposed to be empty.

It doesn't load a dataflow, only a specification that provides IP-cores to the Nodes browser on the sidebar.
:::

```{kpm_iframe}
:spec: https://raw.githubusercontent.com/antmicro/topwrap/main/tests/data/data_kpm/examples/hdmi/specification_hdmi.json
```
(dev-guide-kpm-iframes-usage-local-files)=
### Use local files

```{kpm_iframe}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:height: 80vh
```
(dev-guide-kpm-iframes-usage-preview-mode)=
### Open in preview mode

```{kpm_iframe}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:preview: true
```

(dev-guide-kpm-iframes-usage-alt-text)=
### Use a custom alt text

:::{note}
The alternative text is visible instead of the iframe in the PDF version of this documentation.
:::

```{kpm_iframe}
:spec: ../../../tests/data/data_kpm/examples/hierarchy/specification_hierarchy.json
:dataflow: https://raw.githubusercontent.com/antmicro/topwrap/refs/heads/main/tests/data/data_kpm/examples/hierarchy/dataflow_hierarchy.json
:alt: This diagram showcases the block design of the "hierarchy" example
```
