# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import copy
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar, Iterable, Iterator, Optional

from jinja2 import Template
from typing_extensions import override

from topwrap.backend.backend import Backend, BackendOutputInfo
from topwrap.backend.generator import GeneratorNotImplementedError
from topwrap.backend.sv.common import SVFile, SVFileType, get_template
from topwrap.backend.sv.design import SystemVerilogDesignBackend
from topwrap.backend.sv.generators import verilog_generators_map
from topwrap.model.connections import (
    PortDirection,
)
from topwrap.model.design import Design
from topwrap.model.hdl_types import BitStruct, Logic
from topwrap.model.interconnect import Interconnect
from topwrap.model.interface import (
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
)
from topwrap.model.misc import ObjectId
from topwrap.model.module import Module


@dataclass
class SVOutput:
    #: A name somehow common to all modules and interfaces
    #: useful when all of them are saved in a combined file.
    #: The name of the top module by default.
    base_name: str

    modules: list[SVFile]
    interfaces: list[SVFile]
    package: Optional[SVFile]


class SystemVerilogBackend(Backend[SVOutput]):
    pkg_tmpl: ClassVar[Template] = get_template("package.j2")
    intf_tmpl: ClassVar[Template] = get_template("interface.j2")

    def __init__(
        self,
        existing_interfaces: Iterable[InterfaceDefinition] = (),
        modules: Iterable[Module] = (),
        all_pins: bool = False,
        desc_comms: bool = True,
        mod_stubs: bool = False,
    ) -> None:
        """
        :param all_pins: If True, then all ports in port maps on module instances
            in the design will get explicitly serialized, even if they have nothing
            connected to them. Otherwise only used ports will get serialized in port maps
        :param desc_comms: Adds documentation comments right before the respective
            SV entity declaration containing its description and the generation time
        :param mod_stubs: Additionally generate empty SV module definitions for IR Modules
            in the hierarchy that don't have a design associated (usually meaning they should be
            defined externally). Mainly for debugging purposes.
        """

        super().__init__(existing_interfaces)
        self.all_pins = all_pins
        self.desc_comms = desc_comms
        self.mod_stubs = mod_stubs
        self.modules = {m._id for m in modules}

    @override
    def represent(self, module: Module) -> SVOutput:
        """
        :param module: Top module to represent, its `Design` and components will
        be used to generate SystemVerilog top file.

        :raises GeneratorNotImplementedError: This exception will be raised when an `Interconnect`
            without `Generator` implementation for this `Backend` is encountered in the `Design`
        :raises InterconnectGenerationError: Raised when there is problem with generating HDL code
            in one of `Interconnect`s
        """
        pkg_items = dict[str, Logic]()
        if module.design is not None and len(module.design.interconnects) > 0:
            used_module = copy.deepcopy(module)
        else:
            # `Design` is deepcopied when there is at least one `Interconnect` present,
            # it is because `Interconnect` is converted to `Module` and added to `Design`
            # as `ModuleInstance`, it is needed for generating connections and module instance
            # in SystemVerilog code.
            used_module = module
        intfs = set[ObjectId[InterfaceDefinition]]()
        mods_to_repr = list[Design]()

        existing_ifaces_ids = set([iface.id for iface in self.existing_interfaces])

        def _try_append(log: Logic):
            if log.name is not None and log.name not in pkg_items:
                pkg_items[log.name] = log
            if isinstance(log, BitStruct):
                for field in log.fields:
                    _try_append(field.type)

        for mod in used_module.hierarchy():
            for port in mod.ports:
                _try_append(port.type)
            for intf in mod.interfaces:
                if intf.has_independent_signals:
                    if intf.definition.id not in existing_ifaces_ids:
                        intfs.add(intf.definition._id)
                for sig in intf.signals:
                    _try_append(sig.resolve().type)
            if mod._id not in self.modules or mod._id == used_module._id:
                if mod.design is not None:
                    mods_to_repr.append(mod.design)
                elif self.mod_stubs:
                    des = Design()
                    des.parent = mod
                    mods_to_repr.append(des)

        design = used_module.design

        interconnects = []
        if design is not None:
            interconnects = [self.represent_interconnect(it) for it in design.interconnects]

        pkg = pkg_name = None
        if len(pkg_items) > 0:
            pkg_name = used_module.id.name + "_pkg"
            pkg = self.represent_package(pkg_name, pkg_items)

        # Interconnects need to be added to design before this
        # because represent_design represents top module as well
        modules = [self.represent_design(d, pkg_name) for d in mods_to_repr]

        # interconnects need to be generated before modules are represented
        # but putting them fist in list make it that in generated file
        # thery are also first, it looks bad - top module is somewhere in middle od file
        if len(interconnects) != 0:
            modules.extend(interconnects)

        return SVOutput(
            base_name=used_module.id.name,
            package=pkg,
            interfaces=[self.represent_interface(i.resolve(), pkg_name) for i in intfs],
            modules=modules,
        )

    @override
    def serialize(self, repr: SVOutput, *, combine: bool = False) -> Iterator[BackendOutputInfo]:
        """
        :param combine: Whether to combine all potential SV files into a single one
        """

        if combine:
            pkg = [] if repr.package is None else [repr.package]
            out = "\n\n".join(e.content for e in pkg + repr.interfaces + repr.modules)
            yield BackendOutputInfo(content=out, filename=f"{repr.base_name}.sv")
        else:
            for file in [repr.package] + repr.interfaces + repr.modules:
                if file is not None:
                    yield BackendOutputInfo(content=file.content, filename=f"{file.name}.sv")

    def represent_design(self, des: Design, package_name: Optional[str]) -> SVFile:
        back = SystemVerilogDesignBackend(package_name, self.all_pins, self.desc_comms)
        out = back.serialize(des)
        return SVFile(content=out, type=SVFileType.MODULE, name=des.parent.id.name)

    def represent_interface(
        self, intf: InterfaceDefinition, package_name: Optional[str] = None
    ) -> SVFile:
        modports: dict[InterfaceMode, dict[PortDirection, list[InterfaceSignal]]]
        modports = defaultdict(lambda: defaultdict(lambda: []))
        for sig in intf.signals:
            for mode, conf in sig.modes.items():
                modports[mode][conf.direction].append(sig)

        out = self.intf_tmpl.render(
            intf=intf, modports=modports, package_name=package_name, desc_comms=self.desc_comms
        )

        return SVFile(content=out, type=SVFileType.INTERFACE, name=intf.id.name)

    def represent_package(self, package_name: str, items: dict[str, Logic]) -> SVFile:
        out = self.pkg_tmpl.render(
            name=package_name, items=reversed(items.values()), desc_comms=self.desc_comms
        )
        return SVFile(content=out, type=SVFileType.PACKAGE, name=package_name)

    def represent_interconnect(
        self,
        interconnect: Interconnect,
    ) -> SVFile:
        if type(interconnect) not in verilog_generators_map:
            raise GeneratorNotImplementedError(interconnect, self)

        generator = verilog_generators_map[type(interconnect)]()

        verilog_file = generator.generate(
            interconnect,
            generator.add_module_instance_to_design(interconnect),
        )

        return verilog_file
