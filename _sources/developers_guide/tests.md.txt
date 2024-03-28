# Tests

Topwrap functionality is validated with tests, leveraging the `pytest` library.


## Test execution

Tests are located in the `tests` directory.
All tests can be run with `nox` by specifying the tests session:

```bash
nox -s tests
```

:::{note}
To reuse existing virtual environment and avoid long installation time use `-R` option:

```bash
nox -R -s tests
```
:::

:::{note}
To force a specific Python version and avoid running tests for all listed versions, use `-p VERSION` option:

```bash
nox -p 3.10 -s tests
```
:::

Tests can also be launched without `nox` by executing:
```bash
pytest
```
