# Code style

Automatic formatting and linting of the code can be performed with either `nox` or `pre-commit`.

## Lint with nox

After successful setup, `nox` sessions can be executed to perform lint checks:

```bash
nox -s lint
```

This runs `isort`, `black`, `flake8` and `codespell` and fixes almost all formatting and linting problems automatically, but a small minority has to be fixed by hand (e.g. unused imports).

:::{note}
To reuse current virtual environment and avoid long installation time use `-R` option:

```bash
nox -R -s lint
```
:::

:::{note}
pre-commit can also be run from nox:

```bash
nox -s pre_commit
```
:::
## Lint with pre-commit

Alternatively, you can use pre-commit to perform the same job.
`Pre-commit` hooks need to be installed:

```bash
pre-commit install
```

Now, each use of `git commit` in the shell will trigger actions defined in the `.pre-commit-config.yaml` file.
Pre-commit can be easily disabled with a similar command:

```bash
pre-commit uninstall
```

If you wish to run `pre-commit` asynchronously, then use:

```bash
pre-commit run --all-files
```

:::{note}
`pre-commit` by default also runs `nox` with `isort`,`flake8`, `black` and `codespell` sessions
:::

## Tools

Tools used in project for maintaining code style:
* `Nox` is a tool, which simplifies management of Python testing.
[Visit nox website](https://nox.thea.codes/en/stable/)
* `Pre-commit` is a framework for managing and maintaining multi-language pre-commit hooks.
[Visit pre-commit website](https://pre-commit.com/)
* `Black` is a code formatter.
[Visit black website](https://black.readthedocs.io/en/stable/)
* `Flake8` is a tool capable of linting, styling fixes and complexity analysis.
[Visit flake8 website](https://flake8.pycqa.org/en/latest/)
* `Isort` is a Python utility to sort imports alphabetically.
[Visit isort website](https://pycqa.github.io/isort/)
* `Codespell` is a Python tool to fix common spelling mistakes in text files
[Visit codespell repository](https://github.com/codespell-project/codespell)
