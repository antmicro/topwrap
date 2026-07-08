# Setup

It is required for developers to keep the current code style and it is recommended to frequently run tests.

In order to set up the development environment, install all the optional dependency groups as specified in `pyproject.toml`, which also includes `pre-commit`:

```bash
uv sync --extra all
source .venv/bin/activate
```

The `--extra` option is for installing in editable mode - meaning changes in the code under development will be immediately visible when using the package.
