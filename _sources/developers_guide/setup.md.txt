# Setup

It is required for developers to keep code style and recommended to frequently run tests.
In order to setup the developer's environment install optional dependency groups `topwrap-parse`, `tests` and `lint` specified in `pyproject.toml` which include `nox` and `pre-commit`:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[topwrap-parse,tests,lint]"
```

The `-e` option is for installing in editable mode - meaning changes in the code under development will be immediately visible when using the package.
