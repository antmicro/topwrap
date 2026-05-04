# Logging

## Using a Custom Logging Configuration

A custom logging configuration file can be provided with the `--log-cfg` option:

```bash
topwrap --log-cfg logger.cfg build --design {design_name.yaml}
```

Example configuration:

```cfg
[loggers]
keys=root,frontend,backend

[handlers]
keys=rootStreamHandler,rootFileHandler,frontendStreamHandler,frontendFileHandler,backendStreamHandler,backendFileHandler

[formatters]
keys=rootFormatter,frontendFormatter,backendFormatter

[logger_root]
level=DEBUG
handlers=rootStreamHandler,rootFileHandler

[logger_frontend]
level=DEBUG
handlers=frontendFileHandler,frontendStreamHandler
qualname=topwrap.frontend.yaml.frontend
propagate=0

[logger_backend]
level=DEBUG
handlers=backendFileHandler,backendStreamHandler
qualname=topwrap.backend.sv.backend
propagate=0

[handler_rootStreamHandler]
class=StreamHandler
formatter=rootFormatter
args=(sys.stdout,)

[handler_rootFileHandler]
class=FileHandler
formatter=rootFormatter
args=("topwrap.log",)

[handler_frontendStreamHandler]
class=StreamHandler
formatter=frontendFormatter
args=(sys.stdout,)

[handler_frontendFileHandler]
class=FileHandler
formatter=frontendFormatter
args=("topwrap.log","w")

[handler_backendStreamHandler]
class=StreamHandler
formatter=backendFormatter
args=(sys.stdout,)

[handler_backendFileHandler]
class=FileHandler
formatter=backendFormatter
args=("topwrap.log","w")

[formatter_rootFormatter]
format=%(levelname)s:%(message)s

[formatter_frontendFormatter]
format=%(levelname)s:frontend:%(message)s

[formatter_backendFormatter]
format=%(levelname)s:backend:%(message)s
```

If both `--log-level` and `--log-cfg` are provided, the logging configuration file is loaded first, and the log level specified by `--log-level` overrides the configured levels.

## Creating a New Logger

Since Topwrap relies on Python’s standard `logging` module, users can easily add custom loggers.

Each logger should correspond to a Python module and use the module name as its `qualname`.

The module name can be obtained by:
- printing `__name__` inside the module, or
- converting the file path into dotted module notation.

For example:

```text
topwrap/frontend/frontend.py
```

corresponds to:

```text
topwrap.frontend.frontend
```
