# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


from topwrap.backend.yaml.common.interface_schema import (
    InterfaceDefinitionDescription,
    InterfaceDefinitionSignalsDescription,
)
from topwrap.model.connections import PortDirection
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
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
        required_signals = InterfaceDefinitionSignalsDescription.Inner()
        optional_signals = InterfaceDefinitionSignalsDescription.Inner()
        for signal in definition.signals:
            if InterfaceMode.MANAGER in signal.modes:
                configuration = signal.modes[InterfaceMode.MANAGER]
            else:
                configuration = signal.modes[InterfaceMode.UNSPECIFIED]
            if configuration.required:
                if configuration.direction == PortDirection.IN:
                    required_signals.input[signal.name] = signal.regexp
                elif configuration.direction == PortDirection.OUT:
                    required_signals.output[signal.name] = signal.regexp
                elif configuration.direction == PortDirection.INOUT:
                    required_signals.inout[signal.name] = signal.regexp
                else:
                    raise AssertionError("Not implemented, should not be possible")
            else:
                if configuration.direction == PortDirection.IN:
                    optional_signals.input[signal.name] = signal.regexp
                elif configuration.direction == PortDirection.OUT:
                    optional_signals.output[signal.name] = signal.regexp
                elif configuration.direction == PortDirection.INOUT:
                    optional_signals.inout[signal.name] = signal.regexp
                else:
                    raise AssertionError("Not implemented, should not be possible")
        iface_def = InterfaceDefinitionDescription(
            id=definition.id,
            signals=InterfaceDefinitionSignalsDescription(
                required=required_signals,
                optional=optional_signals,
            ),
        )
        return iface_def
