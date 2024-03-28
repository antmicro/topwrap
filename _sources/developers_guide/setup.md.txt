# Setup

It is recommended for developers to keep code style and frequently run tests.
In order to setup the developer's environment install optional dependency groups `topwrap-parse`, `tests` and `lint` specified in `pyproject.toml` which include `nox` and `pre-commit`:

```bash
python -m venv venv
source venv/bin/activate
pip install ".[topwrap-parse,tests,lint]"
```
