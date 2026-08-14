# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


from typing import Optional

from topwrap.backend.yaml.common.interface_schema import (
    InterfaceDefinitionDescription,
    InterfaceDefinitionSignalDescription,
    InterfaceDefinitionSignalMode,
)
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignalConfiguration,
)


class InterfaceDefinitionDescriptionBackend:
    """
    Converts InterfaceDefinition to InterfaceDefinitionDescription.
    Is used when InterfaceDefinition IR class needs to be saved to YAML file.
    """

    def represent(self, definition: InterfaceDefinition) -> InterfaceDefinitionDescription:
        """
        Represent IR `InterfaceDefinition` in InterfaceDefinitionDescription YAML

        :param definition: InterfaceDefinition IR class that will be represented as
            InterfaceDefinitionDescription YAML file
        """

        def _repr_mode(
            conf: Optional[InterfaceSignalConfiguration],
        ) -> Optional[InterfaceDefinitionSignalMode]:
            if not conf:
                return None
            return (conf.direction.value, "required" if conf.required else "optional")

        signals = {}
        for sig in definition.signals:
            mmode = sig.modes.get(InterfaceMode.MANAGER)
            smode = sig.modes.get(InterfaceMode.SUBORDINATE)
            umode = sig.modes.get(InterfaceMode.UNSPECIFIED)

            # Skip representing subordinate mode if it can be inferred from manager mode.
            if mmode is not None and mmode.reverse() == smode:
                smode = None

            # Skip representing unspecified mode if it can be inferred from manager mode.
            if mmode is not None and mmode == umode:
                umode = None

            modes = {}
            if mmode is not None:
                modes["manager"] = _repr_mode(mmode)
            if smode is not None:
                modes["subordinate"] = _repr_mode(smode)
            if umode is not None:
                modes["unspecified"] = _repr_mode(umode)

            signals[sig.name] = InterfaceDefinitionSignalDescription(
                pattern=sig.regexp,
                modes=modes,
                default=sig.default and sig.default.value,
            )

        return InterfaceDefinitionDescription(
            id=definition.id,
            signals=signals,
        )
