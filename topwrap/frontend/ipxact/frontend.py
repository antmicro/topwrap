# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

import topwrap_ipxact_parser as ipxact

from topwrap.frontend.frontend import (
    Frontend,
    FrontendMetadata,
    FrontendParseException,
    FrontendParseOutput,
)
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedInterface,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    Dimensions,
    LogicBitSelect,
    LogicFieldSelect,
    LogicSelect,
)
from topwrap.model.interface import (
    Interface,
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, Identifier, ObjectId, Parameter
from topwrap.model.module import Module


class IpXactFrontend(Frontend):
    @property
    def metadata(self):
        return FrontendMetadata(name="IP-XACT", file_association=[".xml"])

    def _replace_uuid_with_param_name(self, v: str, parameters: Dict[str, Parameter]) -> str:
        """Replace uuid_[uuid] with name of parameter"""
        tokens = re.findall(r"uuid_\w*|\d|[-+*\/]", v)
        for token in tokens:
            if token in parameters:
                param = parameters[token]
                v = v.replace(token, param.name)
        return v

    def _parse_component_ports(
        self,
        comp: ipxact.componentType,
        ir_module: Module,
        parameter_id_to_parameter: Dict[str, Parameter],
    ):
        if comp.model and comp.model.ports and comp.model.ports.port:
            for port in comp.model.ports.port:
                name = port.name
                if port.wire is None:
                    raise FrontendParseException(
                        f"Port '{name}' has no wire element; only wire ports are supported"
                    )
                if port.wire.direction == "in":
                    dir = PortDirection.IN
                elif port.wire.direction == "out":
                    dir = PortDirection.OUT
                else:
                    dir = PortDirection.INOUT
                if port.wire.vectors:
                    dims = []
                    for vector in port.wire.vectors.vector:
                        left = vector.left.get_valueOf_()
                        right = vector.right.get_valueOf_()
                        left_ir = self._replace_uuid_with_param_name(
                            left, parameter_id_to_parameter
                        )
                        right_ir = self._replace_uuid_with_param_name(
                            right, parameter_id_to_parameter
                        )
                        dims.append(
                            Dimensions(
                                upper=ElaboratableValue(left_ir),
                                lower=ElaboratableValue(right_ir),
                            )
                        )
                    ir_type = Bits(dimensions=dims)
                else:
                    ir_type = Bit()
                port = Port(name=name, direction=dir, type=ir_type)
                ir_module.add_port(port)
        return parameter_id_to_parameter

    def _check_if_vlnv_exists(self, obj: Any, err_message: str = "tag don't exists"):
        for field in ("vendor", "library", "name", "version"):
            if getattr(obj, field) is None:
                raise FrontendParseException(f"{field} {err_message}")

    def _find_or_raise(self, view: Any, name: str, kind: str, context: str) -> Any:
        result = view.find_by_name(name)
        if result is None:
            raise FrontendParseException(f"Can't find {kind} '{name}' in {context}")
        return result

    def _vlnv_to_identifier(self, vlnv: Any, err_message: str = "tag don't exists") -> Identifier:
        self._check_if_vlnv_exists(vlnv, err_message)
        return Identifier(
            vendor=vlnv.vendor, library=vlnv.library, name=vlnv.name, version=vlnv.version
        )

    def _parse_component(
        self, comp: ipxact.componentType, iface_definitions: Dict[Identifier, InterfaceDefinition]
    ) -> Tuple[Module, Dict[str, Parameter]]:
        """Returns parsed module and dict with UUIDs mapped to parameters"""
        id = self._vlnv_to_identifier(comp)
        ir_module = Module(id=id)

        # component has two concept of parameters, one for IPXACT parameters and second for RTL
        # parameters
        rtl_parameters: Dict[str, str] = {}  # uuid, name

        if (
            comp.model
            and comp.model.instantiations
            and comp.model.instantiations.componentInstantiation
            and len(comp.model.instantiations.componentInstantiation) >= 1
        ):
            instation = comp.model.instantiations.componentInstantiation[0]
            if instation.moduleParameters and instation.moduleParameters.moduleParameter:
                for parameter in instation.moduleParameters.moduleParameter:
                    name = parameter.name
                    uuid = parameter.value.valueOf_
                    rtl_parameters[uuid] = name

        parameter_id_to_parameter: Dict[str, Parameter] = {}

        if comp.parameters and comp.parameters.parameter:
            for parameter in comp.parameters.parameter:
                uuid = parameter.parameterId
                # When there isn't rtl parameter for that IPXACT parameter
                if uuid not in rtl_parameters:
                    continue
                name = rtl_parameters[uuid]
                default_value = parameter.value.get_valueOf_()
                parameter_ir = Parameter(name=name, default_value=ElaboratableValue(default_value))
                ir_module.add_parameter(parameter_ir)
                parameter_id_to_parameter[uuid] = parameter_ir

        self._parse_component_ports(comp, ir_module, parameter_id_to_parameter)

        if comp.busInterfaces:
            for busInterface in comp.busInterfaces.busInterface:
                name = busInterface.name
                type_id = self._vlnv_to_identifier(
                    busInterface.busType, "missing in a VLNV reference"
                )

                if type_id not in iface_definitions:
                    raise FrontendParseException(
                        f"Can't find interface definition '{type_id}' "
                        f"in available interface definitions"
                    )
                ir_iface_def = iface_definitions[type_id]

                if busInterface.abstractionTypes is None:
                    raise FrontendParseException(f"busInterface '{name}' has no abstractionTypes")
                abstractionType = busInterface.abstractionTypes.abstractionType[
                    0
                ]  # Assumption: Only one abstraction type, IR can't represent more
                mode = (
                    InterfaceMode.MANAGER
                    if busInterface.initiator
                    else InterfaceMode.SUBORDINATE
                    if busInterface.target
                    else InterfaceMode.UNSPECIFIED
                )
                iface_signals: Dict[ObjectId[InterfaceSignal], Optional[ReferencedPort]] = {}
                for portMap in abstractionType.portMaps.portMap:
                    logicalPort = portMap.logicalPort
                    physicalPort = portMap.physicalPort
                    iface_signal = self._find_or_raise(
                        ir_iface_def.signals,
                        logicalPort.name,
                        "signal",
                        f"interface definition '{type_id}', that is present "
                        f"in '{id}' module as '{name}' interface",
                    )
                    # All ports need to be defined in model.ports in ipxact
                    ir_port = self._find_or_raise(
                        ir_module.ports,
                        physicalPort.name,
                        "port",
                        f"module {id}",
                    )
                    # BitSelect operates on the physical port. Generate it only when
                    # a partSelect is provided (otherwise the mapping covers the whole
                    # port and needs no selection) and the physical port is not a
                    # scalar ``Bit`` (slicing a 1-bit signal is not representable in IR).
                    ops: List[Union[LogicFieldSelect, LogicBitSelect]] = []
                    if physicalPort.partSelect and not isinstance(ir_port.type, Bit):
                        ps = physicalPort.partSelect.range_
                        up = int(ps.left.get_valueOf_())
                        down = int(ps.right.get_valueOf_())
                        ops.append(
                            LogicBitSelect(
                                Dimensions(ElaboratableValue(up), ElaboratableValue(down))
                            )
                        )

                    select = LogicSelect(logic=ir_port.type, ops=ops) if ops else None
                    iface_signals[iface_signal._id] = ReferencedPort.external(ir_port, select)
                ir_iface = Interface(
                    name=name, mode=mode, definition=ir_iface_def, signals=iface_signals
                )
                ir_module.add_interface(ir_iface)

        return ir_module, parameter_id_to_parameter

    def _parse_design_interconnections(self, des: ipxact.design, module: Module, ir_des: Design):
        if des.interconnections:
            for interconnection in des.interconnections.interconnection:
                ref_ifaces = []
                for interface in interconnection.activeInterface:
                    mod_name = interface.componentInstanceRef
                    iface_name = interface.busRef
                    if mod_name is not None:
                        ir_component = self._find_or_raise(
                            ir_des.components,
                            mod_name,
                            "module instance",
                            f"design '{module.id}'",
                        )
                        ir_interface = self._find_or_raise(
                            ir_component.module.interfaces,
                            iface_name,
                            "interface",
                            f"instance module '{ir_component.name}' that is instance of "
                            f"'{ir_component.module.id}'",
                        )
                    else:
                        ir_component = None
                        ir_interface = self._find_or_raise(
                            module.interfaces,
                            iface_name,
                            "interface",
                            f"module '{module.id}'",
                        )
                    ref_ifaces.append(ReferencedInterface(instance=ir_component, io=ir_interface))

                for hierIface in interconnection.hierInterface:
                    iface_name = hierIface.busRef
                    iface = self._find_or_raise(
                        module.interfaces,
                        iface_name,
                        "interface",
                        f"module '{module.id}'",
                    )
                    ref_ifaces.append(ReferencedInterface.external(iface))

                conn = InterfaceConnection(ref_ifaces[0], ref_ifaces[1])
                ir_des.add_connection(conn)

    def _parse_design_adHocConnections(self, des: ipxact.design, module: Module, ir_des: Design):
        if des.adHocConnections:
            for adHocConnection in des.adHocConnections.adHocConnection:
                ref_ports = []
                for port in adHocConnection.portReferences.internalPortReference:
                    mod_name = port.componentInstanceRef
                    port_name = port.portRef
                    ir_component = self._find_or_raise(
                        ir_des.components,
                        mod_name,
                        "module instance",
                        f"design '{module.id}'",
                    )
                    ir_port = self._find_or_raise(
                        ir_component.module.ports,
                        port_name,
                        "port",
                        f"instance module '{ir_component.name}' that is instance of "
                        f"'{ir_component.module.id}'",
                    )
                    ref_ports.append(ReferencedPort(instance=ir_component, io=ir_port))

                for port in adHocConnection.portReferences.externalPortReference:
                    port_name = port.portRef
                    ir_component = None
                    ir_port = self._find_or_raise(
                        module.ports, port_name, "port", f"module '{module.id}'"
                    )
                    ref_ports.append(ReferencedPort(instance=None, io=ir_port))

                if adHocConnection.tiedValue:
                    if len(ref_ports) != 1:
                        raise FrontendParseException(
                            f"Connection '{adHocConnection.name}' in design"
                            f"'{module.id}' has too many port references"
                        )
                    conn = ConstantConnection(
                        ElaboratableValue(adHocConnection.tiedValue.get_valueOf_()), ref_ports[0]
                    )
                else:
                    if len(ref_ports) != 2:
                        raise FrontendParseException(
                            f"Connection '{adHocConnection.name}' in design "
                            f"'{module.id}' need to have two ports"
                        )
                    conn = PortConnection(ref_ports[0], ref_ports[1])

                ir_des.add_connection(conn)

    def _parse_design(
        self,
        des: ipxact.design,
        module: Module,
        modules: Dict[Identifier, Module],
        uuid_to_param: Dict[str, Parameter],
    ):
        ir_des = Design()
        # `ir_des.parent` need to be set by caller

        if des.componentInstances:
            for componentInstance in des.componentInstances.componentInstance:
                name = componentInstance.instanceName
                component_ref = componentInstance.componentRef
                module_id = self._vlnv_to_identifier(component_ref, "missing in a VLNV reference")
                if module_id not in modules:
                    raise FrontendParseException(f"Can't find '{module_id}' in available modules")
                ir_module = modules[module_id]
                ir_module_instance = ModuleInstance(name=name, module=ir_module)
                configurable_elements = componentInstance.componentRef.configurableElementValues
                if configurable_elements:
                    for param in configurable_elements.configurableElementValue:
                        uuid = param.referenceId
                        value = param.valueOf_
                        if uuid not in uuid_to_param:
                            raise FrontendParseException(
                                f"Can't find parameter for configurableElementValue "
                                f"reference '{uuid}' in instance '{name}'"
                            )
                        ir_param = uuid_to_param[uuid]
                        ir_module_instance.parameters[ir_param._id] = ElaboratableValue(value)
                ir_des.add_component(ir_module_instance)

        self._parse_design_interconnections(des, module, ir_des)
        self._parse_design_adHocConnections(des, module, ir_des)

        return ir_des

    def _parse_abstraction_definition(
        self, definition: ipxact.abstractionDefinition
    ) -> InterfaceDefinition:
        signals = []
        if definition.ports:
            for port in definition.ports.port:
                name = port.logicalName
                modes = {
                    InterfaceMode.MANAGER: InterfaceSignalConfiguration(PortDirection.INOUT, True),
                    InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                        PortDirection.INOUT, True
                    ),
                    InterfaceMode.UNSPECIFIED: InterfaceSignalConfiguration(
                        PortDirection.INOUT, True
                    ),
                }
                width = Bit()
                if port.wire:
                    wire = port.wire
                    if wire.onInitiator:
                        required = wire.onInitiator.presence == "required"
                        direction = (
                            PortDirection.OUT
                            if wire.onInitiator.direction == "out"
                            else PortDirection.IN
                        )
                        modes[InterfaceMode.MANAGER] = InterfaceSignalConfiguration(
                            direction, required
                        )
                        # Overwrite
                        modes[InterfaceMode.UNSPECIFIED] = modes[InterfaceMode.MANAGER]

                        # Overwrite, assumption is that onTarget and onInitiator has same width
                        # No width means "unconstrained"; keep the default Bit().
                        if wire.onInitiator.width is not None:
                            width_val = int(wire.onInitiator.width.get_valueOf_())
                            dims = [Dimensions(upper=ElaboratableValue(width_val))]
                            width = Bit() if width_val == 1 else Bits(dimensions=dims)
                    if wire.onTarget:
                        required = wire.onTarget.presence == "required"
                        direction = (
                            PortDirection.OUT
                            if wire.onTarget.direction == "out"
                            else PortDirection.IN
                        )
                        modes[InterfaceMode.SUBORDINATE] = InterfaceSignalConfiguration(
                            direction, required
                        )

                signals.append(
                    InterfaceSignal(name=name, regexp=re.compile(name), modes=modes, type=width)
                )

        if definition.busType is None:
            raise FrontendParseException("busType tag don't exist")

        id = self._vlnv_to_identifier(definition.busType, "in busType tag don't exists")

        return InterfaceDefinition(id=id, signals=signals)

    @contextmanager
    def _wrap_parse_errors(self, source: Path) -> Iterator[None]:
        try:
            yield
        except FrontendParseException as e:
            raise FrontendParseException(f"Exception while parsing file '{source}'") from e

    def parse_files(self, sources: Iterable[Path]) -> FrontendParseOutput:
        # parsing component requires all interfaces, but parse_files should output only new
        # interfaces
        all_interface_definitions: Dict[Identifier, InterfaceDefinition] = {
            i.id: i for i in self.interfaces
        }
        ipxact_interface_definitions: Dict[Identifier, InterfaceDefinition] = {}

        parsed_components: List[Tuple[Path, ipxact.componentType]] = []
        parsed_designs_configurations: Dict[Identifier, ipxact.designConfiguration] = {}
        parsed_designs: List[Tuple[Path, ipxact.design]] = []
        modules_with_design: Dict[Identifier, Module] = {}

        for source in sources:
            parsed = ipxact.parse(source, True)
            if isinstance(parsed, ipxact.componentType):
                parsed_components.append((source, parsed))
            elif isinstance(parsed, ipxact.design):
                parsed_designs.append((source, parsed))
            elif isinstance(parsed, ipxact.designConfiguration):
                designRef = parsed.designRef
                designRef_id = self._vlnv_to_identifier(designRef, "missing in a VLNV reference")
                parsed_designs_configurations[designRef_id] = parsed
            elif isinstance(parsed, ipxact.abstractionDefinition):
                with self._wrap_parse_errors(source):
                    interfaceDefinition = self._parse_abstraction_definition(parsed)
                intf_key = interfaceDefinition.id
                all_interface_definitions[intf_key] = interfaceDefinition
                ipxact_interface_definitions[intf_key] = interfaceDefinition

        uuid_to_param: Dict[str, Parameter] = {}
        all_modules: Dict[Identifier, Module] = {m.id: m for m in self.modules}
        ipxact_modules: Dict[Identifier, Module] = {}
        for source, parsed in parsed_components:
            with self._wrap_parse_errors(source):
                module, uuid_to_param_local = self._parse_component(
                    parsed, all_interface_definitions
                )
            all_modules[module.id] = module
            ipxact_modules[module.id] = module
            uuid_to_param.update(uuid_to_param_local)
            if (
                parsed.model
                and parsed.model.instantiations
                and parsed.model.instantiations.designConfigurationInstantiation
            ):
                # Should check the view tag and then get the
                # designConfigurationInstantiation by the name
                # but IR can't represent multiple views of same design
                # so it isn't supported
                design_conf_ref = parsed.model.instantiations.designConfigurationInstantiation[
                    0
                ].designConfigurationRef
                design_conf_id = self._vlnv_to_identifier(
                    design_conf_ref, "missing in a VLNV reference"
                )
                modules_with_design[design_conf_id] = module

        for source, parsed in parsed_designs:
            design_id = self._vlnv_to_identifier(parsed, "missing in a VLNV reference")
            if design_id not in parsed_designs_configurations:
                raise FrontendParseException(
                    f"Can't find design configuration for design '{design_id}'"
                )
            parsed_design_conf = parsed_designs_configurations[design_id]
            design_conf_id = self._vlnv_to_identifier(
                parsed_design_conf, "missing in a VLNV reference"
            )
            if design_conf_id not in modules_with_design:
                raise FrontendParseException(
                    f"Can't find module for design configuration '{design_conf_id}'"
                )
            module_with_that_design = modules_with_design[design_conf_id]
            with self._wrap_parse_errors(source):
                ir_des = self._parse_design(
                    parsed, module_with_that_design, all_modules, uuid_to_param
                )
            module_with_that_design.design = ir_des

        return FrontendParseOutput(
            interfaces=list(ipxact_interface_definitions.values()),
            modules=list(ipxact_modules.values()),
        )
