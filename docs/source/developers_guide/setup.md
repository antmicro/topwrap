# Setup

It is required for developers to keep the current code style and it is recommended to frequently run tests.

In order to set up the development environment, install all the optional dependency groups as specified in `pyproject.toml`, which also includes `pre-commit`:

```bash
uv sync --extra all
source .venv/bin/activate
```

The `--extra` option is for installing in editable mode - meaning changes in the code under development will be immediately visible when using the package.

## Using custom KPM versions

Topwrap uses a prebuilt KPM wheel. If you need a custom commit, change the dependencies list entry `pipeline_manager @ URL` to `pipeline_manager`, and add an entry to the tools section:

```toml
[tools.uv.sources]
pipeline_manager = { git = KPM_REPO_URL, rev = KPM_COMMIT_SHA}
```

where `KPM_REPO_URL` is the desired remote and `KPM_COMMIT_SHA` is the remote.
