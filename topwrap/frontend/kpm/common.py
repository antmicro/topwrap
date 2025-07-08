# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pipeline_manager.dataflow_builder.entities import Direction as KpmDirection

from topwrap.backend.kpm.common import (
    ConstMetanode,
    IdentifierMetanode,
    InterconnectMetanode,
    IoMetanode,
)
from topwrap.frontend.frontend import FrontendParseException
from topwrap.model.connections import PortDirection
from topwrap.model.interface import InterfaceMode
from topwrap.model.misc import TranslationError


class KpmFrontendParseException(FrontendParseException):
    pass


def is_metanode(node_name: str) -> bool:
    return node_name in [
        ConstMetanode.name,
        IoMetanode.name,
        InterconnectMetanode.name,
        IdentifierMetanode.name,
    ]


def kpm_dir_to_ir_port(dir: KpmDirection) -> PortDirection:
    return {
        dir.INPUT: PortDirection.IN,
        dir.OUTPUT: PortDirection.OUT,
        dir.INOUT: PortDirection.INOUT,
    }[dir]


def kpm_dir_to_ir_intf(dir: KpmDirection) -> InterfaceMode:
    res = {dir.INPUT: InterfaceMode.SUBORDINATE, dir.OUTPUT: InterfaceMode.MANAGER}.get(dir)

    if res is None:
        raise TranslationError(f"Cannot translate '{dir}' into {InterfaceMode}")

    return res
