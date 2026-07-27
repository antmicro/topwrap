# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from ast import literal_eval

from pipeline_manager.dataflow_builder.entities import Direction as KpmDirection

from topwrap.backend.kpm.common import (
    ClockDomainMetanode,
    ConstMetanode,
    IdentifierMetanode,
    InterconnectMetanode,
    InverterMetanode,
    IoMetanode,
    ResetDomainMetanode,
)
from topwrap.backend.yaml.common.ip_core_schema import IPCoreComplexParameter
from topwrap.frontend.frontend import FrontendParseException
from topwrap.model.connections import PortDirection
from topwrap.model.interface import InterfaceMode
from topwrap.model.misc import ElaboratableValue, TranslationError


class KpmFrontendParseException(FrontendParseException):
    pass


def is_metanode(node_name: str) -> bool:
    return node_name in [
        ConstMetanode.name,
        IoMetanode.name,
        InterconnectMetanode.name,
        IdentifierMetanode.name,
        InverterMetanode.name,
        ClockDomainMetanode.name,
        ResetDomainMetanode.name,
    ]


def kpm_dir_to_ir_port(dir: KpmDirection) -> PortDirection:
    return {
        dir.INPUT: PortDirection.IN,
        dir.OUTPUT: PortDirection.OUT,
        dir.INOUT: PortDirection.INOUT,
    }[dir]


def kpm_dir_to_ir_intf(dir: KpmDirection) -> InterfaceMode:
    res = {
        dir.INPUT: InterfaceMode.SUBORDINATE,
        dir.OUTPUT: InterfaceMode.MANAGER,
        dir.INOUT: InterfaceMode.UNSPECIFIED,
    }.get(dir)

    if res is None:
        raise TranslationError(f"Cannot translate '{dir}' into {InterfaceMode}")

    return res


def kpm_val_to_elab_val(kpm_val: str) -> ElaboratableValue:
    try:
        return ElaboratableValue(int(kpm_val))
    except ValueError:  # thrown when string cannot be converted to integer
        pass

    try:
        d = literal_eval(kpm_val)
        if isinstance(d, dict):
            return ElaboratableValue(IPCoreComplexParameter(width=d["width"], value=d["value"]))
    except (ValueError, SyntaxError):
        pass

    return ElaboratableValue(kpm_val)
