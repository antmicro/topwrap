# Code style

Automatic formatting and linting of the code is performed with either `Nox` or `pre-commit`.

## Lint with nox

After successful setup, `Nox` sessions can be executed to perform lint checks:

```bash
nox -s lint
```

This runs `isort`, `black`, `flake8` and `codespell` and fixes almost all formatting and linting problems automatically, but a small number must be fixed by hand (e.g. unused imports).

:::{note}
To reuse the current virtual environment and avoid lengthy installation processes, use the `-R` flag:

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

Alternatively, you can use `pre-commit` to perform the same job.
`pre-commit` hooks need to be installed:

```bash
pre-commit install
```

Now, each use of `git commit` in the shell will trigger actions defined in the `.pre-commit-config.yaml` file.
`pre-commit` is easily deactivated with a similar command:

```bash
pre-commit uninstall
```

If you wish to run `pre-commit` asynchronously, then use:

```bash
pre-commit run --all-files
```

:::{note}
`pre-commit` by default also runs `nox` with `isort`, `flake8`, `black` and `codespell` sessions.
:::

## Tools

Tools used in the Topwrap project for maintaining the code style:
* `Nox` is a tool, which simplifies management of Python testing.
[Visit the nox website](https://nox.thea.codes/en/stable/)
* `pre-commit` is a framework for managing and maintaining multi-language pre-commit hooks.
[Visit the pre-commit website](https://pre-commit.com/)
* `Black` is a code formatter.
[Visit the black website](https://black.readthedocs.io/en/stable/)
* `Flake8` is a tool capable of linting, styling fixes and complexity analysis.
[Visit the flake8 website](https://flake8.pycqa.org/en/latest/)
* `Isort` is a Python utility to sort imports alphabetically.
[Visit the isort website](https://pycqa.github.io/isort/)
* `Codespell` is a Python tool to fix common spelling mistakes in text files
[Visit the codespell repository](https://github.com/codespell-project/codespell)
