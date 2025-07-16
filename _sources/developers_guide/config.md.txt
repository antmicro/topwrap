# Config

The {class}`~topwrap.config.Config` object stores configuration values. The global `topwrap.config.Config` object is used throughout the codebase to access the Topwrap configuration.

It is created by {class}`~topwrap.config.ConfigManager` that reads the config files as defined in {attr}`topwrap.config.ConfigManager.DEFAULT_SEARCH_PATHS`, with local files taking precedence.

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
