import copy
import logging
import queue
import re
import uuid
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Set, Tuple

import topwrap_ipxact_parser as ipxact
from typing_extensions import override

from topwrap.backend.backend import Backend, BackendOutputInfo, BackendParseException
from topwrap.backend.generator import GeneratorNotImplementedError
from topwrap.backend.sv.generators import verilog_generators_map
from topwrap.model.connections import ConstantConnection, InterfaceConnection, Port, PortConnection
from topwrap.model.design import Design
from topwrap.model.hdl_types import LogicArray, LogicBitSelect
from topwrap.model.interface import Interface, InterfaceDefinition, InterfaceMode, InterfaceSignal
from topwrap.model.misc import Identifier, ObjectId, Parameter
from topwrap.model.module import Module

logger = logging.getLogger(__name__)


class StringWriter:
    def __init__(self):
        self.content = ""

    def write(self, msg: str):
        self.content += msg


@dataclass
class IPXACTOutput:
    components: List[ipxact.componentType]
    design: List[Tuple[ipxact.design, ipxact.designInstantiationType]]
    iface_definitions: List[Tuple[ipxact.abstractionDefinition, ipxact.busDefinition]]


class IPXACTBackend(Backend[IPXACTOutput]):
    def __init__(self, existing_interfaces: Optional[Set[Identifier]] = None) -> None:
        super().__init__(existing_interfaces)

    def _replace_parameter_name_with_uuid(
        self, input: str, parameter_to_uuid: Dict[ObjectId[Parameter], str]
    ) -> str:
        name_to_uuid = {
            parameter.resolve().name: parameter_uuid
            for parameter, parameter_uuid in parameter_to_uuid.items()
        }

        return re.sub(
            r"""
            \\\S+                               # escaped identifier
            | "(?:\\.|[^"\\])*"                 # string literal
            | //[^\r\n]*                        # line comment
            | /\*.*?\*/                         # block comment
            | (?<![0-9'])[A-Za-z_][A-Za-z0-9_]* # regular identifier
            """,
            lambda match: name_to_uuid.get(match.group(), match.group()),
            input,
            flags=re.VERBOSE | re.DOTALL,
        )

    def represent_component(
        self, module: Module, parameter_to_uuid: Dict[ObjectId[Parameter], str]
    ) -> ipxact.componentType:
        xact_component = ipxact.componentType()
        xact_component.name = module.id.name
        xact_component.vendor = module.id.vendor
        xact_component.library = module.id.library
        xact_component.version = module.id.version

        xact_component.model = ipxact.modelType()

        if module.design is not None:
            name = f"{module.id.name}.designcfg_{module.id.version}"
            xact_component.model.instantiations = ipxact.instantiationsType(
                designConfigurationInstantiation=[
                    ipxact.designConfigurationInstantiationType(
                        name=name,
                        designConfigurationRef=ipxact.configurableLibraryRefType(
                            name=f"{module.id.name}.designcfg",
                            vendor=module.id.vendor,
                            library=module.id.library,
                            version=module.id.version,
                        ),
                    )
                ]
            )
            xact_component.model.views = ipxact.viewsType(
                view=[
                    ipxact.viewType(name="hierarchical", designConfigurationInstantiationRef=name)
                ]
            )

        xact_busInterfaces, additional_ports = self._build_bus_interfaces(module)

        if len(xact_busInterfaces) > 0:
            xact_component.busInterfaces = ipxact.busInterfaces(busInterface=xact_busInterfaces)

        xact_params = []
        xact_moduleParams = []
        parameter_to_uuid_local = {}

        def is_value_int(value: str) -> bool:
            try:
                int(value)
            except ValueError:
                return False
            return True

        for parameter in module.parameters:
            xact_uuid = f"uuid_{str(uuid.uuid4()).replace('-', '_')}"
            xact_param = ipxact.parameterType(parameterId=xact_uuid, name=parameter.name)
            if parameter.default_value is None:
                # FIXME: Kactus2 don't accept 0 or None when param is used to calculate width of
                # port
                xact_param.value = ipxact.stringExpression("1")
                xact_param.type_ = "longint"
            else:
                xact_param.value = ipxact.stringExpression(parameter.default_value.value)
                xact_param.type_ = (
                    "longint" if is_value_int(parameter.default_value.value) else "string"
                )
            parameter_to_uuid_local[parameter._id] = xact_uuid
            parameter_to_uuid[parameter._id] = xact_uuid
            xact_params.append(xact_param)
            xact_moduleParams.append(
                ipxact.moduleParameterType(
                    name=parameter.name,
                    displayName=parameter.name,
                    value=ipxact.stringExpression(xact_uuid),
                    parameterId=f"uuid_{str(uuid.uuid4()).replace('-', '_')}",
                )
            )

        if len(xact_params) > 0:
            xact_component.parameters = ipxact.parameters(parameter=xact_params)

        if module.design is None:
            xact_instation = ipxact.componentInstantiationType(name="rtl", displayName="rtl")
            xact_component.model.instantiations = ipxact.instantiationsType(
                componentInstantiation=[xact_instation]
            )
            if len(xact_moduleParams) > 0:
                xact_instation.moduleParameters = ipxact.moduleParametersType(
                    moduleParameter=xact_moduleParams
                )

        xact_ports = self._build_ports(module, additional_ports, parameter_to_uuid_local)

        xact_component.model.ports = ipxact.portsType152(port=xact_ports)

        return xact_component

    def _build_bus_interfaces(
        self, module: Module
    ) -> Tuple[List[ipxact.busInterfaceType], Dict[str, Port]]:
        xact_busInterfaces = []
        # Port that are created when there is independent interface signal
        additional_ports: Dict[str, Port] = {}

        for iface in module.interfaces:
            iface_def = iface.definition
            xact_bus = ipxact.busInterfaceType(
                name=iface.name,
                busType=ipxact.configurableLibraryRefType(
                    name=iface_def.id.name,
                    vendor=iface_def.id.vendor,
                    library=iface_def.id.library,
                    version=iface_def.id.version,
                ),
            )
            if iface.mode == InterfaceMode.MANAGER:
                xact_bus.initiator = ipxact.initiatorType()
            elif iface.mode == InterfaceMode.SUBORDINATE:
                xact_bus.target = ipxact.targetType()
            elif iface.mode == InterfaceMode.UNSPECIFIED:
                xact_bus.initiator = ipxact.initiatorType()
                logger.warning(
                    f"Encountered UNSPECIFIED interface type in interface {iface.name}"
                    f"in module {module.id.combined()}"
                )

            xact_portMaps = []
            for signal in iface.definition.signals:
                if signal._id not in iface.signals:
                    continue
                xact_portMaps.append(
                    self._build_signal_port_map(iface, signal, module, additional_ports)
                )

            if len(xact_portMaps) > 0:
                xact_bus.abstractionTypes = ipxact.abstractionTypes(
                    abstractionType=[
                        ipxact.abstractionTypeType(
                            portMaps=ipxact.portMapsType(portMap=xact_portMaps),
                            abstractionRef=ipxact.configurableLibraryRefType(
                                name=f"{iface_def.id.name}.absDef",
                                vendor=iface_def.id.vendor,
                                library=iface_def.id.library,
                                version=iface_def.id.version,
                            ),
                        )
                    ]
                )

            xact_busInterfaces.append(xact_bus)

        return xact_busInterfaces, additional_ports

    def _build_signal_port_map(
        self,
        iface: Interface,
        signal: InterfaceSignal,
        module: Module,
        additional_ports: Dict[str, Port],
    ) -> ipxact.portMapType:
        ref_port = iface.signals[signal._id]
        physicalPartSelect = None

        if ref_port is None:
            # Try to find port of that name that already exists
            port = module.ports.find_by_name(signal.name)
            if port is None:
                if signal.name in additional_ports:
                    port = additional_ports[signal.name]
                else:
                    # If there isn't any create one
                    port = Port(
                        name=signal.name,
                        direction=signal.modes[iface.mode].direction,
                        type=signal.type,
                        default_value=signal.default,
                    )
                    additional_ports[signal.name] = port
        else:
            port = ref_port.io
            if len(ref_port.select.ops) > 1:
                raise BackendParseException("Multi dim select not supported")

            if len(ref_port.select.ops) == 1:
                if not isinstance(ref_port.select.ops[0], LogicBitSelect):
                    raise BackendParseException("Structs not supported")

                slice = ref_port.select.ops[0].slice
                physicalPartSelect = ipxact.partSelect(
                    range_=ipxact.range_(
                        left=ipxact.unsignedIntExpression(valueOf_=slice.upper.value),
                        right=ipxact.unsignedIntExpression(valueOf_=slice.lower.value),
                    )
                )

        return ipxact.portMapType(
            logicalPort=ipxact.logicalPortType(
                name=signal.name,
            ),
            physicalPort=ipxact.physicalPortType(name=port.name, partSelect=physicalPartSelect),
        )

    def _build_ports(
        self,
        module: Module,
        additional_ports: Dict[str, Port],
        parameter_to_uuid_local: Dict[ObjectId[Parameter], str],
    ) -> List[ipxact.port]:
        xact_ports = []
        for port in [*module.ports, *additional_ports.values()]:
            vectors = []
            if isinstance(port.type, LogicArray):
                for dim in port.type.dimensions:
                    vectors.append(
                        ipxact.vectorType25(
                            left=ipxact.unsignedIntExpression(
                                valueOf_=self._replace_parameter_name_with_uuid(
                                    dim.upper.value, parameter_to_uuid_local
                                )
                            ),
                            right=ipxact.unsignedIntExpression(
                                valueOf_=self._replace_parameter_name_with_uuid(
                                    dim.lower.value, parameter_to_uuid_local
                                )
                            ),
                        )
                    )
            extendedVectors = None
            if len(vectors) > 0:
                extendedVectors = ipxact.extendedVectorsType(vector=vectors)
            xact_port = ipxact.port(
                name=port.name,
                wire=ipxact.portWireType(direction=port.direction.value, vectors=extendedVectors),
            )
            xact_ports.append(xact_port)

        return xact_ports

    def _represent_design_connections(
        self, des: Design
    ) -> Tuple[list[ipxact.adHocConnection], list[ipxact.interconnection]]:
        xact_connections = []
        xact_interfaces = []
        for conn in des.connections:
            if isinstance(conn, InterfaceConnection):
                xact_interface = ipxact.interconnection()
                target_name = conn.target.io.name
                target_instance = (
                    None if conn.target.instance is None else conn.target.instance.name
                )
                source_name = conn.source.io.name
                source_instance = (
                    None if conn.source.instance is None else conn.source.instance.name
                )
                xact_interface.activeInterface = []
                xact_interface.hierInterface = []
                if target_instance is None:
                    xact_interface.hierInterface.append(
                        ipxact.hierInterfaceType(busRef=target_name)
                    )
                else:
                    xact_interface.activeInterface.append(
                        ipxact.activeInterface(
                            componentInstanceRef=target_instance, busRef=target_name
                        )
                    )
                if source_instance is None:
                    xact_interface.hierInterface.append(
                        ipxact.hierInterfaceType(busRef=source_name)
                    )
                else:
                    xact_interface.activeInterface.append(
                        ipxact.activeInterface(
                            componentInstanceRef=source_instance, busRef=source_name
                        )
                    )

                if not xact_interface.activeInterface:
                    raise ValueError(
                        "Interconnection must have at least one active (non-external) interface"
                    )

                def gen_name(instance_name: Optional[str]) -> str:
                    return f"{instance_name}_" if instance_name is not None else ""

                xact_interface.name = (
                    f"{gen_name(target_instance)}{target_name}"
                    f"_to_{gen_name(source_instance)}{source_name}"
                )

                xact_interfaces.append(xact_interface)
            else:
                name = ""
                xact_connection = ipxact.adHocConnection()
                xact_internal_port_refs: List[ipxact.internalPortReferenceType] = []
                xact_external_port_refs: List[ipxact.externalPortReference] = []

                if conn.target.instance is not None:
                    xact_internal_port_refs.append(
                        ipxact.internalPortReferenceType(
                            portRef=conn.target.io.name,
                            componentInstanceRef=conn.target.instance.name,
                        )
                    )
                    name += f"{conn.target.instance.name}_{conn.target.io.name}"
                else:
                    xact_external_port_refs.append(
                        ipxact.externalPortReference(portRef=conn.target.io.name)
                    )
                    name += f"{conn.target.io.name}"
                name += "_to_"
                if isinstance(conn, PortConnection):
                    if conn.source.instance is not None:
                        xact_internal_port_refs.append(
                            ipxact.internalPortReferenceType(
                                portRef=conn.source.io.name,
                                componentInstanceRef=conn.source.instance.name,
                            )
                        )
                        name += f"{conn.source.instance.name}_{conn.source.io.name}"
                    else:
                        xact_external_port_refs.append(
                            ipxact.externalPortReference(portRef=conn.source.io.name)
                        )
                        name += f"{conn.source.io.name}"
                elif isinstance(conn, ConstantConnection):
                    xact_connection.tiedValue = ipxact.complexTiedValueExpression(
                        valueOf_=conn.source.value
                    )
                    name += "tiedValue"

                xact_connection.portReferences = ipxact.portReferencesType(
                    internalPortReference=xact_internal_port_refs,
                    externalPortReference=xact_external_port_refs,
                )
                xact_connection.name = name

                xact_connections.append(xact_connection)
        return xact_connections, xact_interfaces

    def represent_design(
        self, des: Design, parameter_to_uuid: Dict[ObjectId[Parameter], str]
    ) -> Tuple[ipxact.design, ipxact.designConfiguration]:
        parent_module_id = des.parent.id
        xact_design = ipxact.design(
            name=f"{parent_module_id.name}.design",
            vendor=parent_module_id.vendor,
            library=parent_module_id.library,
            version=parent_module_id.version,
        )

        xact_componentInstance = []
        for component in des.components:
            module_id = component.module.id
            xact_component_ref = ipxact.configurableLibraryRefType(
                name=module_id.name,
                vendor=module_id.vendor,
                library=module_id.library,
                version=module_id.version,
            )

            paramsArray = []
            for param in component.parameters:
                value = component.parameters[param]
                uuid_value = parameter_to_uuid[param]
                paramsArray.append(
                    ipxact.configurableElementValue(referenceId=uuid_value, valueOf_=value)
                )
            xact_component_ref.configurableElementValues = ipxact.configurableElementValues(
                configurableElementValue=paramsArray
            )

            xact_comp = ipxact.componentInstance(
                instanceName=component.name, componentRef=xact_component_ref
            )
            xact_componentInstance.append(xact_comp)

        xact_design.componentInstances = ipxact.componentInstances(
            componentInstance=xact_componentInstance
        )

        xact_conns, xact_interfaces = self._represent_design_connections(des)
        xact_design.interconnections = ipxact.interconnections(interconnection=xact_interfaces)
        xact_design.adHocConnections = ipxact.adHocConnections(adHocConnection=xact_conns)

        xact_design_cfg = ipxact.designConfiguration(
            name=f"{xact_design.name}cfg",
            vendor=xact_design.vendor,
            library=xact_design.library,
            version=xact_design.version,
            designRef=ipxact.libraryRefType(
                name=xact_design.name,
                vendor=xact_design.vendor,
                library=xact_design.library,
                version=xact_design.version,
            ),
        )

        return xact_design, xact_design_cfg

    def represent_iface(
        self, iface_def: InterfaceDefinition
    ) -> Tuple[ipxact.abstractionDefinition, ipxact.busDefinition]:
        xact_absDef = ipxact.abstractionDefinition()
        xact_absDef.name = f"{iface_def.id.name}.absDef"
        xact_absDef.library = iface_def.id.library
        xact_absDef.vendor = iface_def.id.vendor
        xact_absDef.version = iface_def.id.version

        xact_ports = []

        for signal in iface_def.signals:
            xact_wire = ipxact.wire()
            xact_width = ipxact.widthType77(valueOf_=signal.type.size.value)
            subordinate_mode = signal.modes[InterfaceMode.SUBORDINATE]
            xact_wire.onTarget = ipxact.onTargetType78(
                presence=ipxact.presenceType(
                    "required" if subordinate_mode.required else "optional"
                ),
                direction=subordinate_mode.direction.value,
                width=xact_width,
            )
            manager_mode = signal.modes[InterfaceMode.MANAGER]
            xact_wire.onInitiator = ipxact.onInitiatorType76(
                presence=ipxact.presenceType("required" if manager_mode.required else "optional"),
                direction=manager_mode.direction.value,
                width=xact_width,
            )
            xact_port = ipxact.portType70(logicalName=signal.name, wire=xact_wire)
            xact_ports.append(xact_port)

        xact_absDef.ports = ipxact.portsType(port=xact_ports)

        xact_absDef.busType = ipxact.libraryRefType(
            vendor=iface_def.id.vendor,
            name=iface_def.id.name,
            version=iface_def.id.version,
            library=iface_def.id.library,
        )

        xact_busDef = ipxact.busDefinition()
        xact_busDef.name = iface_def.id.name
        xact_busDef.library = iface_def.id.library
        xact_busDef.vendor = iface_def.id.vendor
        xact_busDef.version = iface_def.id.version

        return xact_absDef, xact_busDef

    @override
    def represent(self, module: Module) -> IPXACTOutput:
        if module.design is not None and len(module.design.interconnects) > 0:
            used_module = copy.deepcopy(module)
        else:
            # `Design` is deepcopied when there is at least one `Interconnect` present,
            # it is because `Interconnect` is converted to `Module` and added to `Design`
            # as `ModuleInstance`, it is needed for generating connections and module instance
            # in SystemVerilog code.
            used_module = module

        if used_module.design is not None:
            des = used_module.design

            designs_to_parse = queue.SimpleQueue()
            added_modules = set()
            parsed_components = [self.represent_component(used_module, {})]

            iface_definitions = []

            for mod in used_module.hierarchy():
                for iface in mod.interfaces:
                    iface_definitions.append(self.represent_iface(iface.definition))
                if mod.design is not None:
                    for interconnect in mod.design.interconnects:
                        # Reuse system verilog generator
                        # Different HDL backends could generate different IR modules
                        # for example SV generator for wishbone don't create clk and rst signals
                        # when there is only one manager
                        if type(interconnect) not in verilog_generators_map:
                            raise GeneratorNotImplementedError(interconnect, self)

                        generator = verilog_generators_map[type(interconnect)]()
                        generator.add_module_instance_to_design(interconnect)

            parsed_designs = []

            designs_to_parse.put(des)
            while not designs_to_parse.empty():
                parameter_to_uuid: Dict[ObjectId[Parameter], str] = {}
                current_des = designs_to_parse.get()
                # first parse all components and add designs if present
                for component in current_des.components:
                    current_mod = component.module
                    if current_mod.id.combined() not in added_modules:
                        added_modules.add(current_mod.id.combined())
                        parsed_components.append(
                            self.represent_component(component.module, parameter_to_uuid)
                        )
                        mod_des = current_mod.design
                        if mod_des is not None:
                            designs_to_parse.put(mod_des)
                # once we have all uuid's for parameters, then parse design
                parsed_designs.append(self.represent_design(current_des, parameter_to_uuid))

            return IPXACTOutput(parsed_components, parsed_designs, iface_definitions)
        else:
            iface_definitions = []
            for iface in used_module.interfaces:
                iface_definitions.append(self.represent_iface(iface.definition))
            return IPXACTOutput([self.represent_component(used_module, {})], [], iface_definitions)

    @override
    def serialize(self, repr: IPXACTOutput) -> Iterator[BackendOutputInfo]:
        for entry in repr.design:
            design, design_cfg = entry
            writer = StringWriter()
            design.export(writer, 0)
            yield BackendOutputInfo(filename=f"{design.name}.xml", content=writer.content)
            writer = StringWriter()
            design_cfg.export(writer, 0)
            yield BackendOutputInfo(filename=f"{design_cfg.name}.xml", content=writer.content)
        for component in repr.components:
            writer = StringWriter()
            component.export(writer, 0, name_="component")
            yield BackendOutputInfo(filename=f"{component.name}.xml", content=writer.content)
        for iface in repr.iface_definitions:
            absDef, busDef = iface
            writer = StringWriter()
            absDef.export(writer, 0)
            yield BackendOutputInfo(filename=f"{absDef.name}.xml", content=writer.content)
            writer = StringWriter()
            busDef.export(writer, 0)
            yield BackendOutputInfo(filename=f"{busDef.name}.xml", content=writer.content)
