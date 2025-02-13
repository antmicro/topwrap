# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import cache
from typing import (
    Any,
    Iterable,
    Optional,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
    overload,
)

import marshmallow_dataclass
import yaml
from pipeline_manager.dataflow_builder.entities import Direction as KpmDirection

from topwrap.common_serdes import MarshmallowDataclassExtensions, ext_field
from topwrap.model.connections import PortDirection
from topwrap.model.interconnect import (
    _IPAR,
    InterconnectManagerParams,
    InterconnectParams,
    InterconnectSubordinateParams,
)
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


_MANSUB = TypeVar("_MANSUB", bound=Union[InterconnectManagerParams, InterconnectSubordinateParams])


@dataclass
class _MarshMixin(MarshmallowDataclassExtensions):
    pass


class InterconnectParamSerializer:
    """
    This class is used by the KPM backends and frontends to handle representation of the
    IR `Interconnect` using the `InterconnectMetanode`. It allows serialization and
    deserialization of `InterconnectParams`, `InterconnectManagerParams` and
    `InterconnectSubordinateParams` and their derivatives into a YAML-like format that
    is shown and can be edited in a text property in KPM.
    """

    @classmethod
    @cache
    def _get_proxy(
        cls,
        for_: Type[
            Union[InterconnectParams, InterconnectManagerParams, InterconnectSubordinateParams]
        ],
    ) -> Type[_MarshMixin]:
        return marshmallow_dataclass.dataclass(type("proxy", (for_, _MarshMixin), {}))

    @classmethod
    def serialize(
        cls,
        obj: Union[
            InterconnectParams,
            Iterable[InterconnectManagerParams],
            Iterable[InterconnectSubordinateParams],
        ],
    ) -> str:
        @marshmallow_dataclass.dataclass
        class Cleaner(MarshmallowDataclassExtensions):
            inner: dict[Any, Any] = ext_field(deep_cleanup=True)

        if isinstance(obj, InterconnectParams):
            proxy = cls._get_proxy(type(obj))
            victim = proxy(**asdict(obj)).to_dict()
        else:
            victim = {}

            for i, params in enumerate(x for x in obj):
                proxy = cls._get_proxy(type(params))
                victim[i] = proxy(**asdict(params)).to_dict()

        return yaml.safe_dump(Cleaner(victim).to_dict()["inner"], default_flow_style=True).strip()[
            1:-1
        ]

    @overload
    @classmethod
    def deserialize(cls, val: str, into: Type[_IPAR]) -> _IPAR: ...

    @overload
    @classmethod
    def deserialize(cls, val: str, into: Type[_MANSUB]) -> dict[int, _MANSUB]: ...

    @classmethod
    def deserialize(
        cls, val: str, into: Union[Type[_MANSUB], Type[_IPAR]]
    ) -> Union[_IPAR, dict[int, _MANSUB]]:
        proxy = cls._get_proxy(into)
        raw = cast(dict[str, Any], yaml.safe_load("{" + val + "}"))
        if issubclass(into, InterconnectParams):
            return into(**asdict(proxy.from_dict(raw)))
        return {int(i): into(**asdict(proxy.from_dict(par))) for i, par in raw.items()}
