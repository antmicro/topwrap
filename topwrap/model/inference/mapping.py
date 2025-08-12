# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from typing import ClassVar, Sequence, Type

import marshmallow
import marshmallow_dataclass

from topwrap.common_serdes import MarshmallowDataclassExtensions, ext_field
from topwrap.model.inference.port import PortSelectorT
from topwrap.model.interface import Interface, InterfaceDefinition, InterfaceMode
from topwrap.model.misc import Identifier, QuerableView
from topwrap.model.module import Module


@marshmallow_dataclass.dataclass(frozen=True)
class InterfacePortGrouping(MarshmallowDataclassExtensions):
    """
    A grouping of ports that are to be put into one interface.
    """

    #: Identifier of the interface that this grouping uses.
    interface: Identifier = ext_field()

    #: The interface mode (manager, subordinate) for this grouping.
    mode: str = ext_field()

    #: A signal name to port selector mapping for this grouping.
    signals: dict[str, PortSelectorT] = ext_field()


@marshmallow_dataclass.dataclass(frozen=True)
class InterfacePortMapping(MarshmallowDataclassExtensions):
    """
    A mapping between module ports and interface signals.
    """

    #: The identifier of the module this mapping applies to.
    id: Identifier = ext_field()

    #: Named groupings of ports into interfaces.
    #: See :class:`PortSelector` for a description of the format.
    interfaces: dict[str, InterfacePortGrouping] = ext_field(dict)

    Schema: ClassVar[Type[marshmallow.Schema]] = marshmallow.Schema


@marshmallow_dataclass.dataclass(frozen=True)
class InterfacePortMappingDefinition(MarshmallowDataclassExtensions):
    """
    Top level port mapping definition. Can contain mappings for multiple modules.
    """

    modules: list[InterfacePortMapping] = ext_field()


class InterfaceMappingError(RuntimeError):
    """Error raised for problems that occurred during interface mapping."""


def _build_interface(
    module: Module, definition: InterfaceDefinition, name: str, group: InterfacePortGrouping
):
    """
    Construct an interface for the given group and definition, and add it to the module.
    """

    # If the module already has an interface with this name, ignore this group.
    # Assumption: the caller is trying to apply the mapping for a second time.
    if module.interfaces.find_by_name(name):
        return

    mode = InterfaceMode.UNSPECIFIED
    if group.mode == "MANAGER":
        mode = InterfaceMode.MANAGER
    elif group.mode == "SUBORDINATE":
        mode = InterfaceMode.SUBORDINATE

    error_preamble = f"In interface '{name}' of module '{module.id.name}'"

    if mode == InterfaceMode.UNSPECIFIED:
        raise InterfaceMappingError(f"{error_preamble}: unknown interface mode '{group.mode}'")

    signals = {}
    for signal in definition.signals:
        if signal.name not in group.signals:
            if signal.modes[mode].required:
                raise InterfaceMappingError(
                    f"{error_preamble}: required signal '{signal.name}' is not assigned to anything"
                )
            else:
                continue

        try:
            ref_port = group.signals[signal.name].make_referenced_port(module, mode, signal)
        except ValueError as ex:
            raise InterfaceMappingError(f"Bad port selector: {str(ex)}") from ex
        signals.update({signal._id: ref_port})

    intf = Interface(name=name, mode=mode, definition=definition, signals=signals)
    module.add_interface(intf)


def map_interfaces_to_module(
    mappings: Sequence[InterfacePortMapping],
    intf_defs: Sequence[InterfaceDefinition],
    module: Module,
):
    """
    Apply mappings to the given module. Potentially modifies the module by adding new interfaces, as
    described in the given mappings.

    :param mappings: The mappings to use.
    :param intf_defs: Known interface definitions for mappings.
    :param module: Module to apply mappings to.
    """
    intf_defs = QuerableView(intf_defs)

    def _map_interface(mapping: InterfacePortMapping):
        """
        Apply the given mapping to the module.
        """

        for name, group in mapping.interfaces.items():
            intf_def = intf_defs.find_by(lambda d, group=group: d.id == group.interface)
            if not intf_def:
                raise InterfaceMappingError(
                    f"Group {name} of module {module.id.name} references unknown interface "
                    f"{group.interface}"
                )
            _build_interface(module, intf_def, name, group)

    for mapping in mappings:
        if mapping.id == module.id:
            _map_interface(mapping)
