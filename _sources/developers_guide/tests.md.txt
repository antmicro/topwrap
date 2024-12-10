# Tests

Topwrap functionality is validated with tests that leverage the `pytest` library.

## Test execution

The tests are located in the `tests` directory.
All tests can be run with `nox` by specifying the `tests` session:

```bash
nox -s tests
```

This runs tests on the Python interpreter versions that are available locally.
There is also a session `tests_in_env` that will automatically install all required Python versions, provided you have [pyenv](https://github.com/pyenv/pyenv) installed:

```bash
nox -s tests_in_env
```

:::{note}
To reuse an existing virtual environment and avoid lengthy installation times,  use the `-R` flag:

```bash
nox -R -s tests_in_env
```

:::

To force a specific Python version and avoid running tests for all listed versions, use `-p VERSION` flag:

```bash
nox -p 3.10 -s tests_in_env
```

Tests can also be launched without `nox` by executing:

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

For debugging purposes, Pytest captures all output from the test and displays it when all tests are completed.
To see the output immediately, pass the `-s` flag to pytest:

```bash
python -m pytest -s
```

## Test coverage

Test coverage is automatically generated when running tests with `nox`.
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

All `kpm` data from examples can be generated using `nox`.
This is useful when changing Topwrap functionality relating to kpm, as it avoids manually changing test data in every sample.
Users can either update of example data such as the specification or update everything (dataflows, specifications, designs).

To update everything run:
```bash
nox -s update_test_data
```

To update only specifications run:
```bash
nox -s update_test_data -- specification
```

Valid options for `update_test_data` sessions, are:
* `specification`
* `dataflow`
* `design`
