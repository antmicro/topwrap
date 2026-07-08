# Code style

`pre-commit` performs automatic formatting and linting of the code.

## Lint with pre-commit

Alternatively, use `pre-commit` to perform the same job.
`pre-commit` hooks need to be installed:

```bash
pre-commit install
```

Now, each use of `git commit` in the shell will trigger actions defined in the `.pre-commit-config.yaml` file.
`pre-commit` is easily deactivated with a similar command:

```bash
pre-commit uninstall
```

If you wish to run `pre-commit` asynchronously, use:

```bash
pre-commit run --all-files
```

:::{note}
`pre-commit` by default also runs `ruff` and `codespell` sessions.
:::

## Tools

Tools used in the Topwrap project for maintaining the code style:
* [`pre-commit`](https://pre-commit.com/) is a framework for managing and maintaining multi-language pre-commit hooks.
* [`ruff`](https://docs.astral.sh/ruff/) is a Python linter and code formatter.
* [`codespell`](https://github.com/codespell-project/codespell) is a Python tool to fix common spelling mistakes in text files
