# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import importlib.metadata
import logging
from typing import Any

from topwrap.plugin.base import BasePlugin, PluginException

logger = logging.getLogger(__name__)


class PluginManager:
    group: str
    plugins: list[tuple[int, str, BasePlugin]]
    loaded: bool

    def __init__(self, group: str = "topwrap.plugins"):
        self.group = group
        self.plugins = []
        self.loaded = False

    def load_plugins(self):
        """Loads installed plugins"""

        if self.loaded:
            return

        unsorted = []
        for entry in importlib.metadata.entry_points(group=self.group):
            try:
                plugin_cls = entry.load()
                if not issubclass(plugin_cls, BasePlugin):
                    raise TypeError("Must inherit from plugin")
                priority = getattr(plugin_cls, "priority", 0)
                unsorted.append((priority, entry.name, plugin_cls()))
                print(f"Loaded plugin {entry.name}")
            except Exception as e:
                print(f"Error loading {entry.name}: {e}")

        self.plugins = sorted(unsorted, key=lambda x: x[0], reverse=True)
        self.loaded = True

    def trigger(self, hook: Any, *args: Any, **kwargs: Any):
        """Executes hook and passes all arguments to the plugin methods."""

        if not self.loaded:
            raise RuntimeError("load_plugins need to be called before trigger")

        hook_name = hook.__name__
        for priority, name, instance in self.plugins:
            logger.debug(f"Invoking hook {hook_name} from plugin {name} (priority {priority})")

            method = getattr(instance, hook_name, None)
            if callable(method):
                try:
                    method(*args, **kwargs)
                except Exception as e:
                    raise PluginException(
                        f"Exception occurred while running hook {hook_name} from plugin {name}: {str(e)}"
                    ) from e
