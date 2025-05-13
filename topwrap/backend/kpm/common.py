# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, TypedDict, Union

from pipeline_manager.dataflow_builder.entities import Direction as KpmDirection

from topwrap.model.connections import PortDirection
from topwrap.model.interconnects.wishbone_rr import WishboneInterconnect
from topwrap.model.interface import InterfaceMode
from topwrap.model.misc import Identifier, TranslationError


class LayerType(Enum):
    IP_CORE = "IP Cores"
    EXTERNAL = "Externals"
    CONSTANT = "Constants"
    IDENT = "Identifiers"


class KpmConnPattern(Enum):
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


class KpmPropertyType(Enum):
    TEXT = "text"
    CONSTANT = "constant"
    NUMBER = "number"
    INTEGER = "integer"
    SELECT = "select"
    BOOL = "bool"
    SLIDER = "slider"
    LIST = "list"
    HEX = "hex"


PORT_INTF_TYPE = "intf__port"
PORT_COLOR = "#00ca7c"
EXT_COLOR = "#ffffff"
EXT_INTF_TYPE = "intf__ext"
INTF_COLOR = "#5ad1cd"
INTF_CONN_STYLE = KpmConnPattern.DASHED
SUGBRAPH_NODE_NAME = "New Graph Node"


class KpmNodeAdditionalData(TypedDict):
    full_module_id: dict[str, str]


@dataclass
class KpmNodeId:
    name: str
    category: str

    @classmethod
    def from_ir_id(cls, id: Identifier):
        return cls(id.name, f"{id.vendor}/{id.library}")


def kpm_dir_from(dir: Union[PortDirection, InterfaceMode, str]) -> KpmDirection:
    res = {
        PortDirection.IN: KpmDirection.INPUT,
        PortDirection.OUT: KpmDirection.OUTPUT,
        PortDirection.INOUT: KpmDirection.INOUT,
        InterfaceMode.MANAGER: KpmDirection.OUTPUT,
        InterfaceMode.SUBORDINATE: KpmDirection.INPUT,
        InterfaceMode.UNSPECIFIED: KpmDirection.INOUT,
        KpmDirection.INPUT.value: KpmDirection.INPUT,
        KpmDirection.OUTPUT.value: KpmDirection.OUTPUT,
        KpmDirection.INOUT.value: KpmDirection.INOUT,
    }.get(dir)

    if res is None:
        raise TranslationError(f"Cannot translate '{dir}' into {KpmDirection}")

    return res


@dataclass
class KpmProperty:
    propname: str
    proptype: str
    default: Any
    description: Optional[str] = None
    min: Any = None
    max: Any = None
    values: Optional[list[Any]] = None
    dtype: Optional[str] = None
    override: Optional[bool] = None
    group: Optional[list[KpmProperty]] = None


@dataclass
class KpmInterface:
    interfacename: str
    direction: str = "inout"
    interfacetype: Optional[Union[str, list[str]]] = None
    dynamic: Union[bool, list[int]] = False
    side: Optional[str] = None
    maxcount: Optional[int] = None
    override: Optional[bool] = None
    array: Optional[list[int]] = None


@dataclass
class Metanode:
    name: str
    category = "Metanode"
    layer: Optional[LayerType] = None
    interfaces: list[KpmInterface] = field(default_factory=list)
    properties: list[KpmProperty] = field(default_factory=list)


@dataclass
class IoMetanode(Metanode):
    name: str = "External I/O"
    layer: Optional[LayerType] = LayerType.EXTERNAL
    interfaces: list[KpmInterface] = field(
        default_factory=lambda: [
            KpmInterface("in", KpmDirection.INPUT.value),
            KpmInterface("out", KpmDirection.OUTPUT.value),
            KpmInterface("inout", KpmDirection.INOUT.value),
        ]
    )


@dataclass
class ConstMetanode(Metanode):
    name: str = "Constant"
    layer: Optional[LayerType] = LayerType.CONSTANT
    interfaces: list[KpmInterface] = field(
        default_factory=lambda: [
            KpmInterface("constant", KpmDirection.OUTPUT.value, interfacetype=PORT_INTF_TYPE)
        ]
    )
    properties: list[KpmProperty] = field(
        default_factory=lambda: [KpmProperty("Constant Value", KpmPropertyType.TEXT.value, "0")]
    )


class InterconnectMetanodeStrings(Enum):
    CLK_PORT = "clk"
    RST_PORT = "rst"
    MAN_INTF = "manager"
    SUB_INTF = "subordinate"
    TYPE_PROP = "Type"
    ADV_PROP = "Advanced configuration"
    INTR_CONF_PROP = "Interconnect configuration"
    INTR_MAN_CONF_PROP = "Managers configuration"
    INTR_SUB_CONF_PROP = "Subordinates configuration"


class InterconnectTypes(Enum):
    WISHBONE_RR = WishboneInterconnect


IMS = InterconnectMetanodeStrings


@dataclass
class InterconnectMetanode(Metanode):
    name: str = "Interconnect"
    interfaces: list[KpmInterface] = field(
        default_factory=lambda: [
            KpmInterface(
                IMS.CLK_PORT.value,
                KpmDirection.INPUT.value,
                interfacetype=PORT_INTF_TYPE,
                maxcount=1,
            ),
            KpmInterface(
                IMS.RST_PORT.value,
                KpmDirection.INPUT.value,
                interfacetype=PORT_INTF_TYPE,
                maxcount=1,
            ),
            KpmInterface(IMS.MAN_INTF.value, KpmDirection.INPUT.value, dynamic=True, maxcount=1),
            KpmInterface(IMS.SUB_INTF.value, KpmDirection.OUTPUT.value, dynamic=True, maxcount=1),
        ]
    )
    properties: list[KpmProperty] = field(
        default_factory=lambda: [
            KpmProperty(
                IMS.TYPE_PROP.value,
                KpmPropertyType.SELECT.value,
                values=[InterconnectTypes._member_names_],
                default=InterconnectTypes.WISHBONE_RR.name,
            ),
            KpmProperty(
                IMS.ADV_PROP.value,
                KpmPropertyType.BOOL.value,
                False,
                group=[
                    KpmProperty(
                        IMS.INTR_CONF_PROP.value,
                        KpmPropertyType.TEXT.value,
                        default="",
                    ),
                    KpmProperty(
                        IMS.INTR_MAN_CONF_PROP.value,
                        KpmPropertyType.TEXT.value,
                        default="",
                    ),
                    KpmProperty(
                        IMS.INTR_SUB_CONF_PROP.value,
                        KpmPropertyType.TEXT.value,
                        default="",
                    ),
                ],
            ),
        ]
    )


@dataclass
class IdentifierMetanode(Metanode):
    name: str = "Identifier"
    layer: Optional[LayerType] = LayerType.IDENT
    properties: list[KpmProperty] = field(
        default_factory=lambda: [
            KpmProperty("Name", KpmPropertyType.TEXT.value, ""),
            KpmProperty("Vendor", KpmPropertyType.TEXT.value, Identifier(name="").vendor),
            KpmProperty("Library", KpmPropertyType.TEXT.value, Identifier(name="").library),
        ]
    )
