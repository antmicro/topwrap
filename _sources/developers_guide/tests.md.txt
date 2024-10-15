# Tests

Topwrap functionality is validated with tests, leveraging the `pytest` library.


## Test execution

Tests are located in the `tests` directory.
All tests can be run with `nox` by specifying the `tests` session:

```bash
nox -s tests
```

This only runs tests on python interpreter versions that are available locally.
There is also a session `tests_in_env` that will automatically install all required python versions, provided you have [pyenv](https://github.com/pyenv/pyenv) installed:

```bash
nox -s tests_in_env
```

:::{note}
To reuse existing virtual environment and avoid long installation time use `-R` option:

```bash
nox -R -s tests_in_env
```
:::

To force a specific Python version and avoid running tests for all listed versions, use `-p VERSION` option:

```bash
nox -p 3.10 -s tests_in_env
```

Tests can also be launched without `nox` by executing:
```bash
python -m pytest
```

:::{warning}
When running tests by invoking `pytest` directly, tests are ran only on the locally selected python interpreter.
As CI runs them on all supported Python versions it's recommended to run tests with `nox` on all versions before pushing.
:::

Ignoring particular test can be done with `--ignore=test_path`, e.g:
```bash
python -m pytest --ignore=tests/tests_build/test_interconnect.py
```

Sometimes it's useful to see what's being printed by the test for debugging purposes.
Pytest captures all output from the test and displays it when all tests finish.
To see the output immediately, pass `-s` option to pytest:
```bash
python -m pytest -s
```

## Test coverage

Test coverage is automatically generated when running tests with `nox`.
When invoking `pytest` directly it can be generated with `--cov=topwrap` option.
This will generate a summary of coverage displayed in CLI.

```bash
python -m pytest --cov=topwrap
```

Additionally, the summary can be generated in HTML with `--cov=topwrap --cov-report html`, where lines that were not covered by tests can be browsed:

```bash
python -m pytest --cov=topwrap --cov-report html
```

Generated report is available at `htmlcov/index.html`

## Updating kpm test data

All kpm data from examples can be generated using nox.
This is useful when changing topwrap functionality related to kpm in order to avoid manually changing every example's test data.
You can either update only one part of examples data like specification or update everything (dataflows, specifications, designs).

To update everything run:
```bash
nox -s update_test_data
```

To update only specifications run:
```bash
nox -s update_test_data -- specification
```

Possible options for `update_test_data` session:
* `specification` - updates specifications
* `dataflow` - updates dataflows
* `design` - updates designs
