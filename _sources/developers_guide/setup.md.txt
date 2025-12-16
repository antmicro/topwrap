# Setup

It is required for developers to keep the current code style and it is recommended to frequently run tests.

In order to set up the development environment, install all the optional dependency groups as specified in `pyproject.toml`, which also includes `nox` and `pre-commit`:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[all]"
```

The `-e` option is for installing in editable mode - meaning changes in the code under development will be immediately visible when using the package.
