# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import logging
import re
from typing import Optional

from topwrap.backend.yaml.common.interface_schema import (
    InterfaceDefinitionDescription,
    InterfaceDefinitionSignalMode,
    InterfaceDefinitionSignalsDescription,
)
from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import Bit
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, Identifier


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

        if isinstance(desc.signals, InterfaceDefinitionSignalsDescription):
            return self._parse_old(desc.id, desc.signals)

        intf = InterfaceDefinition(id=desc.id)
        for name, sigdef in desc.signals.items():

            def _parse_mode(
                mode: Optional[InterfaceDefinitionSignalMode],
            ) -> Optional[InterfaceSignalConfiguration]:
                if mode is None:
                    return None
                else:
                    dir, req = mode
                    return InterfaceSignalConfiguration(PortDirection(dir), req == "required")

            mmode = _parse_mode(sigdef.modes.get("manager"))
            smode = _parse_mode(sigdef.modes.get("subordinate"))
            umode = _parse_mode(sigdef.modes.get("unspecified"))

            if mmode is not None and smode is None:
                smode = mmode.reverse()
            if smode is not None and mmode is None:
                mmode = smode.reverse()
            if mmode is not None and umode is None:
                umode = mmode

            modes = {}
            if mmode is not None:
                modes[InterfaceMode.MANAGER] = mmode
            if smode is not None:
                modes[InterfaceMode.SUBORDINATE] = smode
            if umode is not None:
                modes[InterfaceMode.UNSPECIFIED] = umode

            intf.add_signal(
                InterfaceSignal(
                    name=name,
                    type=Bit(),
                    regexp=re.compile(sigdef.pattern),
                    modes=modes,
                    default=ElaboratableValue(sigdef.default)
                    if sigdef.default is not None
                    else None,
                )
            )

        return intf

    def _parse_old(
        self, id: Identifier, signals: InterfaceDefinitionSignalsDescription
    ) -> InterfaceDefinition:
        """
        Parse InterfaceDefinitionDescription YAML to IR ``InterfaceDefinition``.

        :param desc: InterfaceDefinitionDescription from YAML file that will be parsed into
            InterfaceDefinition IR class
        """

        logging.warning(f"Interface definition {id.combined} is using the old syntax!")

        intf = InterfaceDefinition(id=id)
        for req, sigs in ((True, signals.required), (False, signals.optional)):
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
