# Config

A {class}`~topwrap.config.Config` object stores configuration values.
A global `topwrap.config.config` object is used throughout the codebase to access topwrap's configuration.
This is created by {class}`~topwrap.config.ConfigManager` that reads config files defined in {attr}`topwrap.config.ConfigManager.DEFAULT_SEARCH_PATHS`, with files most local to the project taking precedence.

```{eval-rst}
.. autoclass:: topwrap.config.Config
   :members:

   .. automethod:: __init__
```

```{eval-rst}
.. autoclass:: topwrap.config.ConfigManager
   :members:

   .. automethod:: __init__
```
