# Validation of design

One of topwrap features is to run validation on user's design which consists of series of checks for errors user may do while creating a design.


```{eval-rst}
.. autoclass:: topwrap.kpm_dataflow_validator.DataflowValidator
   :members:
```

Each check returns the following class:

```{eval-rst}
.. autoclass:: topwrap.kpm_dataflow_validator.CheckResult
```

## Tests for validation checks

Tests for the `DataflowValidator` class are done using various designs that are valid or have some errors in them with the goal to check everything validation functions can do.

Below are all the graphs that are used for testing.

### Duplicate IP names
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_duplicate_ip_names
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_pwm.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_duplicate_ips.json
:preview: True
```

### Invalid parameters' values
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_invalid_parameters_values
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_pwm.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_invalid_params.json
:preview: True
```

### Connection between external Metanodes
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_ext_in_to_ext_out_connections
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_pwm.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_meta_to_meta_conn.json
:preview: True
```

### Ports connected to multiple external Metanodes
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_ports_multiple_external_metanodes
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_pwm.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_port_to_multiple_external_metanodes.json
:preview: True
```

### Duplicate Metanode names
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_duplicate_metanode_names
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_pwm.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_duplicate_metanode_names.json
:preview: True
```

### Duplicate Metanode connected to interface
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_duplicate_external_input_interfaces
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_pwm.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_duplicate_ext_input_ifaces.json
```

### Unnamed Metanodes
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_unnamed_metanodes
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_pwm.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_connected_unnamed_metanode.json
:preview: True
```

### Connection between two inout ports
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_inouts_connections
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_inout.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_inouts_connections.json
:preview: True
```

### Unconnected ports in subgraph node
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_unconn_hierarchy
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_unconn_hierarchy.json
```

### Connection of subgraph node to multiple External Metanodes
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_subgraph_multiple_external_metanodes
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_subgraph_multiple_external_metanodes.json
```

### Connection to subgraph Metanode
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_conn_subgraph_metanode
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_conn_subgraph_metanode.json
```

### Complex hierarchy graph
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_complex_hierarchy
```

```{kpm_iframe}
:spec: ../../../tests/data/data_kpm/conversions/complex/specification_complex.json
:dataflow: ../../../tests/data/data_kpm/conversions/complex/dataflow_complex.json
```

### Duplicate IP cores in subgraph node
```{eval-rst}
.. autofunction:: tests_kpm.test_kpm_validation.dataflow_hier_duplicate_names
```

```{kpm_iframe}
:spec: ../../build/kpm_jsons/spec_hierarchy.json
:dataflow: ../../../tests/data/data_kpm/dataflow_tests/dataflow_hierarchical_duplicate_names.json
```
