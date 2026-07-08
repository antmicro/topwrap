# Tests

Topwrap functionality is validated with tests that leverage the `pytest` library.

## Test execution

The tests are located in the `tests` directory.
All tests can be run with `just` by specifying the `test` task:

```bash
just test
```

:::

To force a specific Python version and avoid running tests for all listed versions, use `test:default` task:

```bash
just test:default:3.10
```

Tests can also be launched without `just` by executing:

```bash
python -m pytest
```

:::{warning}
When running tests by invoking `pytest` directly, tests are ran only on the locally selected Python interpreter.
As the CI runs on all supported Python versions, it's recommended to run tests with `nox` on all versions before pushing.
:::

Ignoring a particular test can be performed with `--ignore=test_path`, e.g:

```bash
python -m pytest --ignore=tests/tests_build/test_interconnect.py
```

To run a specific test, use the `-k test_name` flag, e.g:

```bash
python -m pytest -k TestKpmSpecificationBackend
```

For debugging purposes, Pytest captures all output from the test and displays it when all tests are completed.
To see the output immediately, pass the `-s` flag to pytest:

```bash
python -m pytest -s
```

## Test coverage

Test coverage is automatically generated when running tests with `just`.
When invoking `pytest` directly, it can be generated with the `--cov=topwrap` flag.
This will generate a summary of coverage, displayed in the CLI.

```bash
python -m pytest --cov=topwrap
```

Additionally, the summary can be generated in HTML with the flags `--cov=topwrap --cov-report html`, where lines that were not covered by tests can be browsed:

```bash
python -m pytest --cov=topwrap --cov-report html
```

The generated report is available at `htmlcov/index.html`

## Updating kpm test data

All `kpm` data from examples can be generated using `just`.
This is useful when changing Topwrap functionality relating to kpm, as it avoids manually changing test data in every sample.
Users can either update of example data such as the specification or update everything (dataflows, specifications).

To update everything run:
```bash
just update_testdata --dataflow
```

To update only specifications run:
```bash
just update_testdata --specification
```

Valid options for `update_test_data` sessions, are:
* `specification`
* `dataflow`
