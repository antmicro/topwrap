# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import re

from topwrap.backend.yaml.common.interface_schema import InterfaceDefinitionDescription
from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import Bit
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)


class InterfaceDefinitionDescriptionFrontend:
    """
    Converts InterfaceDefinitionDescription to InterfaceDefinition.
    Is used when InterfaceDefinition IR class needs to be loaded from YAML file.
    """

    def parse(self, desc: InterfaceDefinitionDescription) -> InterfaceDefinition:
        """
        Parse InterfaceDefinitionDescription YAML to IR ``InterfaceDefinition``.

        :param desc: InterfaceDefinitionDescription from YAML file that will be parsed into
            InterfaceDefinition IR class
        """
        intf = InterfaceDefinition(id=desc.id)
        for req, sigs in ((True, desc.signals.required), (False, desc.signals.optional)):
            for dir, dirsigs in (
                (PortDirection.IN, sigs.input.items()),
                (PortDirection.OUT, sigs.output.items()),
                (PortDirection.INOUT, sigs.inout.items()),
            ):
                for name, regex in dirsigs:
                    intf.add_signal(
                        InterfaceSignal(
                            name=name,
                            type=Bit(),
                            regexp=re.compile(regex),
                            modes={
                                InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                                    direction=dir, required=req
                                ),
                                InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                                    direction=dir.reverse(), required=req
                                ),
                                InterfaceMode.UNSPECIFIED: InterfaceSignalConfiguration(
                                    direction=dir, required=req
                                ),
                            },
                        )
                    )

        return intf
