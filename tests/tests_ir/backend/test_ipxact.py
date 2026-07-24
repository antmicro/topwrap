import re
from pathlib import Path
from typing import Any, Counter, Dict, List, Optional, Tuple

import pytest
from deepdiff import DeepDiff
from lxml import etree as ET
from xmldiff import actions as xmldiff_actions
from xmldiff import main as xmldiff
from xmldiff.actions import (
    DeleteAttrib,
    InsertAttrib,
    InsertNamespace,
    InsertNode,
    MoveNode,
    RenameNode,
    UpdateAttrib,
    UpdateTextAfter,
    UpdateTextIn,
)

from examples.ir_examples.modules import (
    intf_top,
    intr_top,
    simp_top,
)
from topwrap.backend.ipxact.backend import IPXACTBackend
from topwrap.model.misc import Parameter
from topwrap.model.module import Module

IPXACT_NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

EXPECTED_PORTMAP_RANGE_DIFF = (
    "{'type_changes': {\"root['io']['portMaps'][1]['logicalRange']\": "
    "{'old_type': <class 'tuple'>, 'new_type': <class 'NoneType'>, "
    "'old_value': ('3', '0'), 'new_value': None}}}"
)


class TestIpxactInternals:
    def test_replacing_parameters(self):
        back = IPXACTBackend()
        uuids = {Parameter(name="WIDTH")._id: "someuuid"}
        replaced = back._replace_parameter_name_with_uuid("(WIDTH + 1) * 2 - 1", uuids)
        assert replaced == "(someuuid + 1) * 2 - 1"

    def test_does_not_replace_parameter_name_in_scientific_notation(self):
        back = IPXACTBackend()
        uuids = {Parameter(name="e3")._id: "someuuid"}

        replaced = back._replace_parameter_name_with_uuid("1e3", uuids)

        assert replaced == "1e3"

    def test_preserves_whitespace_terminating_escaped_identifier(self):
        back = IPXACTBackend()

        replaced = back._replace_parameter_name_with_uuid(r"\WIDTH + 1", {})

        assert replaced == r"\WIDTH + 1"


class TestIpxactIrExamples:
    @staticmethod
    def filter_empty_strings(value: Any):
        if isinstance(value, UpdateTextIn):
            update_text_in: xmldiff_actions.UpdateTextIn = value
            oldtext = update_text_in.oldtext
            text = update_text_in.text
            if ((oldtext is not None and oldtext.isspace()) or oldtext is None) and (
                (text is not None and text.isspace()) or text is None
            ):
                return False
        if isinstance(value, UpdateTextAfter):
            update_text_after: xmldiff_actions.UpdateTextAfter = value
            oldtext = update_text_after.oldtext
            text = update_text_after.text
            if ((oldtext is not None and oldtext.isspace()) or oldtext is None) and (
                (text is not None and text.isspace()) or text is None
            ):
                return False
        return True

    @staticmethod
    def filter_schema_location(value: Any) -> bool:
        if isinstance(value, InsertNamespace):
            if value.prefix == "xsi":
                return False

        if isinstance(value, (InsertAttrib, UpdateAttrib, DeleteAttrib)):
            if "schemaLocation" in value.name:
                return False

        return True

    @staticmethod
    def filter_ad_hoc_connections(value: Any) -> bool:
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))

        path = node + " " + target

        if "ipxact:adHocConnection" in path:
            return False

        return True

    @staticmethod
    def filter_configurable_elements(value: Any) -> bool:
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))

        path = node + " " + target

        if "ipxact:configurableElementValue" in path:
            return False

        return True

    @staticmethod
    def filter_interconnections(value: Any) -> bool:
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))

        path = f"{node} {target}"

        if "ipxact:interconnection" in path:
            return False

        return True

    @staticmethod
    def filter_bus_interfaces(value: Any) -> bool:
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))

        path = f"{node} {target}"

        if "ipxact:busInterface" in path:
            return False

        return True

    @staticmethod
    def is_uuid_text(s: str | None) -> bool:
        return s is not None and "uuid" in s

    @staticmethod
    def filter_unsuported_fileset(value: Any) -> bool:
        if isinstance(value, UpdateTextIn):
            if "fileSets" in value.node:
                return False

        if isinstance(value, InsertNode):
            if "fileSets" in value.target:
                return False

            if value.tag == f"{{{IPXACT_NS}}}fileSets":
                return False

        return True

    @staticmethod
    def filter_unsuported_module_patameters_attributes(value: Any) -> bool:
        if isinstance(value, InsertAttrib):
            if (
                "ipxact:componentInstantiation/ipxact:moduleParameters" in value.node
                and value.name == "type"
            ):
                return False
        return True

    @staticmethod
    def filter_unsuported_parameter_name_display_name(value: Any) -> bool:
        if isinstance(value, InsertNode):
            if (
                "ipxact:parameters/ipxact:parameter" in value.target
                and "ipxact:model" not in value.target
                and value.tag
                in {
                    f"{{{IPXACT_NS}}}name",
                    f"{{{IPXACT_NS}}}displayName",
                }
            ):
                return False

        if isinstance(value, UpdateTextIn):
            if (
                "ipxact:parameters/ipxact:parameter" in value.node
                and "ipxact:model" not in value.node
                and ("ipxact:name" in value.node or "ipxact:displayName" in value.node)
            ):
                return False

        return True

    @staticmethod
    def filter_reference_xmldiff_artifact(value: Any) -> bool:
        if isinstance(value, MoveNode):
            if "ipxact:vectors/ipxact:vector" in value.node and (
                "ipxact:left" in value.node or "ipxact:value" in value.node
            ):
                return False

            if "ipxact:moduleParameters/ipxact:moduleParameter" in value.node and (
                "ipxact:left" in value.node or "ipxact:value" in value.node
            ):
                return False

        if isinstance(value, RenameNode):
            if "ipxact:vectors/ipxact:vector" in value.node and (
                "ipxact:left" in value.node or "ipxact:value" in value.node
            ):
                return False

            if "ipxact:moduleParameters/ipxact:moduleParameter" in value.node and (
                "ipxact:left" in value.node or "ipxact:value" in value.node
            ):
                return False

        return True

    @staticmethod
    def filter_unsuported_parameter_attributes(value: Any) -> bool:
        if isinstance(value, InsertAttrib):
            if "ipxact:parameters/ipxact:parameter" in value.node:
                return False
        return True

    @staticmethod
    def filter_unsupported_drivers(value: Any):
        if isinstance(value, InsertNode):
            target = value.target
            tag = value.tag

            is_driver_related_tag = tag in {
                f"{{{IPXACT_NS}}}drivers",
                f"{{{IPXACT_NS}}}driver",
                f"{{{IPXACT_NS}}}defaultValue",
            }

            is_under_port_wire = (
                "/ipxact:model/ipxact:ports/ipxact:port" in target and "/ipxact:wire" in target
            )

            if is_driver_related_tag and is_under_port_wire:
                return False

        return True

    @staticmethod
    def filter_uuids(value: Any):
        if isinstance(value, UpdateTextIn):
            return not (
                TestIpxactIrExamples.is_uuid_text(value.text)
                or TestIpxactIrExamples.is_uuid_text(value.oldtext)
            )

        if isinstance(value, UpdateAttrib):
            return not (
                TestIpxactIrExamples.is_uuid_text(value.value)
                or TestIpxactIrExamples.is_uuid_text(getattr(value, "oldvalue", None))
            )

        if isinstance(value, InsertAttrib):
            return not TestIpxactIrExamples.is_uuid_text(value.value)

        return True

    @staticmethod
    def filter_unsuported_language_tag(value: Any) -> bool:
        if isinstance(value, UpdateTextIn):
            if "language" in value.node:
                return False
        if isinstance(value, InsertNode):
            if "language" in value.tag:
                return False
        return True

    @staticmethod
    def filter_component_VLNV(value: Any) -> bool:
        if isinstance(value, (UpdateTextIn, RenameNode)):
            node = value.node
            for field in ("vendor", "library", "name", "version"):
                if node == f"/ipxact:component/ipxact:{field}[1]":
                    return False
        return True

    @staticmethod
    def filter_unsupported_model(value: Any) -> bool:
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))
        path = f"{node} {target}"
        if "ipxact:model" in path:
            return False
        return True

    @staticmethod
    def filter_component_artifacts(value: Any) -> bool:
        if isinstance(value, RenameNode):
            node = str(getattr(value, "node", ""))
            if "/ipxact:component/ipxact:" in node:
                return False
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))
        tag = str(getattr(value, "tag", ""))
        path = f"{node} {target} {tag}"
        if "addressSpace" in path:
            return False
        if "/ipxact:component/ipxact:" in node:
            match = re.search(r"/ipxact:component/ipxact:([a-zA-Z]+)", node)
            if match:
                elem = match.group(1)
                if elem not in {
                    "vendor",
                    "library",
                    "name",
                    "version",
                    "busInterfaces",
                    "model",
                }:
                    return False
        return True

    @staticmethod
    def filter_design_component_instances(value: Any) -> bool:
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))
        path = f"{node} {target}"

        if "ipxact:componentInstances" in path or "ipxact:componentInstance" in path:
            if isinstance(value, (MoveNode, UpdateAttrib, UpdateTextIn)):
                return False

        if isinstance(value, UpdateTextIn):
            for field in ("vendor", "library", "name", "version"):
                if node == f"/ipxact:design/ipxact:{field}[1]":
                    return False

        if isinstance(value, RenameNode) and "/ipxact:design/" in node:
            return False

        return True

    @staticmethod
    def get_configurable_element_values(root: ET._Element) -> dict[str, tuple[str, ...]]:
        result = {}

        instances = root.xpath(
            "./ipxact:componentInstances/ipxact:componentInstance",
            namespaces={"ipxact": IPXACT_NS},
        )

        for instance in instances:
            instance_name = instance.findtext(
                "ipxact:instanceName",
                namespaces={"ipxact": IPXACT_NS},
            )

            values = instance.xpath(
                "./ipxact:componentRef/"
                "ipxact:configurableElementValues/"
                "ipxact:configurableElementValue",
                namespaces={"ipxact": IPXACT_NS},
            )

            result[instance_name] = tuple((value.text or "").strip() for value in values)

        return result

    @staticmethod
    def get_ad_hoc_connections(root: ET._Element) -> Counter[Tuple[Any, ...]]:
        connections = []

        connection_nodes = root.xpath(
            "./ipxact:adHocConnections/ipxact:adHocConnection",
            namespaces={"ipxact": IPXACT_NS},
        )

        for connection in connection_nodes:
            endpoints = []

            references = connection.xpath(
                "./ipxact:portReferences/*",
                namespaces={"ipxact": IPXACT_NS},
            )

            for reference in references:
                tag = ET.QName(reference).localname
                port_ref = reference.get("portRef")

                if tag == "internalPortReference":
                    endpoints.append(
                        (
                            "internal",
                            reference.get("componentInstanceRef"),
                            port_ref,
                        )
                    )

                elif tag == "externalPortReference":
                    endpoints.append(
                        (
                            "external",
                            "",
                            port_ref,
                        )
                    )

            connections.append(tuple(sorted(endpoints)))

        return Counter(connections)

    @staticmethod
    def get_interconnections(root: ET._Element, asd: Optional[str] = None) -> List[Any]:
        result = []

        interconnections = root.xpath(
            "./ipxact:interconnections/ipxact:interconnection",
            namespaces={"ipxact": IPXACT_NS},
        )

        for interconnection in interconnections:
            interfaces = []

            active_interfaces = interconnection.xpath(
                "./ipxact:activeInterface",
                namespaces={"ipxact": IPXACT_NS},
            )

            for interface in active_interfaces:
                interfaces.append(
                    (
                        interface.get("componentInstanceRef"),
                        interface.get("busRef"),
                        interface.get("interfaceRef"),
                    )
                )
            result.append(tuple(sorted(interfaces)))

        return sorted(result)

    @staticmethod
    def get_bus_interfaces(root: ET._Element) -> Dict[str, Dict[str, Any]]:
        def _get_range(parent: ET._Element | None) -> Tuple[str, str] | None:
            if parent is None:
                return None
            rng = parent.find(f"{{{IPXACT_NS}}}range")
            if rng is None:
                return None
            left = rng.findtext(f"{{{IPXACT_NS}}}left")
            right = rng.findtext(f"{{{IPXACT_NS}}}right")
            return (left, right)

        result: Dict[str, Dict[str, Any]] = {}
        bus_interfaces = root.xpath(
            "./ipxact:busInterfaces/ipxact:busInterface",
            namespaces={"ipxact": IPXACT_NS},
        )
        for bus_if in bus_interfaces:
            name = bus_if.findtext(f"{{{IPXACT_NS}}}name")
            bus_type = bus_if.find(f"{{{IPXACT_NS}}}busType")
            if bus_if.find(f"{{{IPXACT_NS}}}initiator") is not None:
                mode = "initiator"
            elif bus_if.find(f"{{{IPXACT_NS}}}target") is not None:
                mode = "target"
            else:
                mode = None

            port_maps = []
            for port_map in bus_if.xpath(".//ipxact:portMap", namespaces={"ipxact": IPXACT_NS}):
                logical_port = port_map.find(f"{{{IPXACT_NS}}}logicalPort")
                physical_port = port_map.find(f"{{{IPXACT_NS}}}physicalPort")
                logical_name = (
                    logical_port.findtext(f"{{{IPXACT_NS}}}name")
                    if logical_port is not None
                    else None
                )
                physical_name = (
                    physical_port.findtext(f"{{{IPXACT_NS}}}name")
                    if physical_port is not None
                    else None
                )
                logical_range = _get_range(logical_port)
                part_select = (
                    physical_port.find(f"{{{IPXACT_NS}}}partSelect")
                    if physical_port is not None
                    else None
                )
                physical_range = _get_range(part_select)
                port_maps.append(
                    {
                        "logicalPort": logical_name,
                        "logicalRange": logical_range,
                        "physicalPort": physical_name,
                        "physicalRange": physical_range,
                    }
                )

            result[name] = {
                "mode": mode,
                "busType": {
                    k: (bus_type.get(k) if bus_type is not None else None)
                    for k in ("vendor", "library", "name", "version")
                },
                "portMaps": sorted(port_maps, key=lambda pm: tuple(str(v) for v in pm.values())),
            }

        return result

    @staticmethod
    def get_port_widths_with_name_and_value(
        root: ET._Element,
    ) -> Tuple[Dict[str, Tuple[str, ...]], Dict[str, Tuple[str, ...]]]:
        parameters = root.findall(f"{{{IPXACT_NS}}}parameters/{{{IPXACT_NS}}}parameter")
        uuid2value = {}
        for parameter in parameters:
            uuid2value[parameter.attrib["parameterId"]] = parameter.find(
                f"{{{IPXACT_NS}}}value"
            ).text

        uuid2name = {}
        module_parameters = root.findall(f".//{{{IPXACT_NS}}}moduleParameter")
        for module_parameter in module_parameters:
            name = module_parameter.find(f"{{{IPXACT_NS}}}name").text
            value = module_parameter.find(f"{{{IPXACT_NS}}}value").text
            uuid2name[value] = name

        def replace_str_with_uuid(input_str: str, mapping: Dict[str, str]) -> str:
            tokens = re.findall(r"([a-zA-Z0-9_]+|[+\-*/])", input_str)
            output = ""
            for token in tokens:
                if token in mapping:
                    token = f"{mapping[token]}"
                output += token
            return output

        port2name = {}
        port2value = {}
        ports = root.findall(f".//{{{IPXACT_NS}}}port")
        for port in ports:
            vector = port.find(f"{{{IPXACT_NS}}}wire/{{{IPXACT_NS}}}vectors/{{{IPXACT_NS}}}vector")
            name = port.find(f"{{{IPXACT_NS}}}name").text
            width_name = ()
            width_value = ()
            if vector is not None:
                left = vector.find(f"{{{IPXACT_NS}}}left").text
                right = vector.find(f"{{{IPXACT_NS}}}right").text
                left_name = replace_str_with_uuid(left, uuid2name)
                right_name = replace_str_with_uuid(right, uuid2name)
                left_value = replace_str_with_uuid(left, uuid2value)
                right_value = replace_str_with_uuid(right, uuid2value)

                width_name = (left_name, right_name)
                width_value = (left_value, right_value)
            port2name[name] = width_name
            port2value[name] = width_value

        return port2value, port2name

    @staticmethod
    def filter_widths_by_suffix(
        widths: Dict[str, Tuple[str, ...]], skip_suffixes: Tuple[str, ...]
    ) -> Dict[str, Tuple[str, ...]]:
        """Drop ports whose name ends with any of ``skip_suffixes``.

        Used to exclude interconnect ports whose widths the generator does not
        yet emit (it uses ``Bit()`` from the interface definition), while
        leaving cpu/dsp/mem ports (which carry real ``Bits`` widths) covered.
        """
        return {k: v for k, v in widths.items() if not k.endswith(skip_suffixes)}

    @staticmethod
    def normalize_scalar_vector_widths(
        widths: Dict[str, Tuple[str, ...]],
    ) -> Dict[str, Tuple[str, ...]]:
        """Treat a 1-bit vector ``[0:0]`` as equivalent to a scalar port."""
        return {k: (() if v == ("0", "0") else v) for k, v in widths.items()}

    def test_ir_examples_designs_xmldiffa(self):
        example_path = Path("examples/ir_examples")
        paths = [
            (
                example_path / "simple/ipxact/antmicro.com/simple/top/1.0/top.design.1.0.xml",
                simp_top,
            ),
            (
                example_path / "interface/ipxact/antmicro.com/interface/top/1.0/top.design.1.0.xml",
                intf_top,
            ),
            (
                example_path
                / "interconnect/ipxact/antmicro.com/interconnect/top/1.0/top.design.1.0.xml",
                intr_top,
            ),
        ]

        def filterFunc(value: Any) -> bool:
            return all(
                predicate(value)
                for predicate in [
                    TestIpxactIrExamples.filter_empty_strings,
                    TestIpxactIrExamples.filter_schema_location,
                    TestIpxactIrExamples.filter_ad_hoc_connections,
                    TestIpxactIrExamples.filter_configurable_elements,
                    TestIpxactIrExamples.filter_interconnections,
                    TestIpxactIrExamples.filter_design_component_instances,
                ]
            )

        for path, top_ir in paths:
            if path is None:
                continue

            back = IPXACTBackend()
            repr = back.represent(top_ir)
            out = next(back.serialize(repr))

            output_cont = out.content

            golden_et = ET.parse(path)
            output_et = ET.fromstring(output_cont)

            diff = xmldiff.diff_trees(output_et, golden_et)

            diff_filtered = list(filter(filterFunc, diff))

            golden_params = TestIpxactIrExamples.get_configurable_element_values(golden_et)
            output_params = TestIpxactIrExamples.get_configurable_element_values(output_et)

            assert golden_params == output_params

            golden_connections = TestIpxactIrExamples.get_ad_hoc_connections(golden_et)
            output_connections = TestIpxactIrExamples.get_ad_hoc_connections(output_et)

            assert golden_connections == output_connections

            golden_interconnections = TestIpxactIrExamples.get_interconnections(golden_et, "golden")
            output_interconnections = TestIpxactIrExamples.get_interconnections(output_et, "otuput")

            assert golden_interconnections == output_interconnections

            assert not diff_filtered, "\n".join(str(d) for d in diff_filtered)

    @pytest.mark.parametrize(
        "top, paths_and_diffs, skip_width_suffixes",
        [
            (
                simp_top,
                [
                    (None, None),  # Skip design
                    (None, None),  # Skip design cfg
                    (
                        Path(
                            "examples/ir_examples/simple/ipxact/antmicro.com/simple/top/1.0/top.1.0.xml"
                        ),
                        None,
                    ),
                    (
                        Path(
                            "examples/ir_examples/simple/ipxact/antmicro.com/simple/2mux_compressor/1.0/2mux_compressor.1.0.xml"
                        ),
                        None,
                    ),
                    (
                        Path(
                            "examples/ir_examples/simple/ipxact/antmicro.com/simple/lfsr_gen/1.2/lfsr_gen.1.2.xml"
                        ),
                        None,
                    ),
                ],
                (),
            ),
            (
                intf_top,
                [
                    (None, None),
                    (None, None),
                    (
                        Path(
                            "examples/ir_examples/interface/ipxact/antmicro.com/interface/top/1.0/top.1.0.xml"
                        ),
                        None,
                    ),
                    (
                        Path(
                            "examples/ir_examples/interface/ipxact/antmicro.com/interface/streamer/1.0/streamer.1.0.xml"
                        ),
                        EXPECTED_PORTMAP_RANGE_DIFF,
                    ),
                    (
                        Path(
                            "examples/ir_examples/interface/ipxact/antmicro.com/interface/receiver/1.0/receiver.1.0.xml"
                        ),
                        EXPECTED_PORTMAP_RANGE_DIFF,
                    ),
                ],
                (),
            ),
            (
                intr_top,
                [
                    (None, None),
                    (None, None),
                    (
                        Path(
                            "examples/ir_examples/interconnect/ipxact/antmicro.com/interconnect/top/1.0/top.1.0.xml"
                        ),
                        None,
                    ),
                    (
                        Path(
                            "examples/ir_examples/interconnect/ipxact/antmicro.com/interconnect/cpu/1.0/cpu.1.0.xml"
                        ),
                        None,
                    ),
                    (
                        Path(
                            "examples/ir_examples/interconnect/ipxact/antmicro.com/interconnect/dsp/1.0/dsp.1.0.xml"
                        ),
                        None,
                    ),
                    (
                        Path(
                            "examples/ir_examples/interconnect/ipxact/antmicro.com/interconnect/mem/1.0/mem.1.0.xml"
                        ),
                        None,
                    ),
                    (
                        Path(
                            "examples/ir_examples/interconnect/ipxact/antmicro.com/interconnect/interconnect/interconnect_wishbone_bus.xml"
                        ),
                        None,
                    ),
                    (None, None),  # wishbone.absDef.xml
                    (None, None),  # wishbone.xml
                ],
                ("__adr", "__dat_w", "__dat_r"),
            ),
        ],
    )
    def test_ir_examples_components_xmldiffa(
        self,
        top: Module,
        paths_and_diffs: List[Tuple[Path, Optional[str]]],
        skip_width_suffixes: Tuple[str, ...],
    ):
        back = IPXACTBackend()
        repr = back.represent(top)

        def filterFunc(value: Any) -> bool:
            return all(
                predicate(value)
                for predicate in [
                    TestIpxactIrExamples.filter_unsupported_drivers,
                    TestIpxactIrExamples.filter_unsuported_parameter_attributes,
                    TestIpxactIrExamples.filter_unsuported_module_patameters_attributes,
                    TestIpxactIrExamples.filter_unsuported_fileset,
                    TestIpxactIrExamples.filter_uuids,
                    TestIpxactIrExamples.filter_empty_strings,
                    TestIpxactIrExamples.filter_unsuported_parameter_name_display_name,
                    TestIpxactIrExamples.filter_reference_xmldiff_artifact,
                    TestIpxactIrExamples.filter_unsuported_language_tag,
                    TestIpxactIrExamples.filter_bus_interfaces,
                    TestIpxactIrExamples.filter_schema_location,
                    TestIpxactIrExamples.filter_component_VLNV,
                    TestIpxactIrExamples.filter_unsupported_model,
                    TestIpxactIrExamples.filter_component_artifacts,
                ]
            )

        objects = list(back.serialize(repr))
        for path_and_diff, out in zip(paths_and_diffs, objects, strict=False):
            path, expected_diff = path_and_diff

            if path is None:
                continue

            golden_et = ET.parse(path)
            output_et = ET.fromstring(out.content)

            diff = xmldiff.diff_trees(output_et, golden_et)

            diff_filtered = set(filter(filterFunc, diff))

            golden_bus_interfaces = TestIpxactIrExamples.get_bus_interfaces(golden_et)
            output_bus_interfaces = TestIpxactIrExamples.get_bus_interfaces(output_et)

            bus_iface_diff = DeepDiff(
                golden_bus_interfaces, output_bus_interfaces, ignore_order=True
            )

            if expected_diff is not None:
                assert str(bus_iface_diff) == expected_diff, bus_iface_diff.pretty()
            else:
                assert not bus_iface_diff, bus_iface_diff.pretty()

            golden_port2value, _ = TestIpxactIrExamples.get_port_widths_with_name_and_value(
                golden_et
            )
            output_port2value, _ = TestIpxactIrExamples.get_port_widths_with_name_and_value(
                output_et
            )

            golden_port2value = TestIpxactIrExamples.normalize_scalar_vector_widths(
                TestIpxactIrExamples.filter_widths_by_suffix(golden_port2value, skip_width_suffixes)
            )
            output_port2value = TestIpxactIrExamples.normalize_scalar_vector_widths(
                TestIpxactIrExamples.filter_widths_by_suffix(output_port2value, skip_width_suffixes)
            )

            port_value_diff = DeepDiff(golden_port2value, output_port2value, ignore_order=True)
            assert not port_value_diff, port_value_diff.pretty()

            assert not diff_filtered, "\n".join(str(d) for d in diff_filtered)

    @staticmethod
    def filter_abs_def_ports(value: Any) -> bool:
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))
        path = f"{node} {target}"
        if "ipxact:ports" in path or "ipxact:port[" in path:
            return False
        return True

    @staticmethod
    def filter_bus_def_extras(value: Any) -> bool:
        extras = (
            "description",
            "directConnection",
            "broadcast",
            "isAddressable",
            "systemGroupNames",
            "systemGroupName",
        )
        node = str(getattr(value, "node", ""))
        target = str(getattr(value, "target", ""))
        tag = str(getattr(value, "tag", ""))
        path = f"{node} {target} {tag}"
        for extra in extras:
            if f"ipxact:{extra}" in path or f"}}{extra}" in path:
                return False
        return True

    @staticmethod
    def get_abstraction_definition(root: ET._Element) -> Dict[str, Any]:
        def _direction(parent: ET._Element | None) -> Optional[str]:
            if parent is None:
                return None
            dir_el = parent.findtext(f"{{{IPXACT_NS}}}direction")
            return dir_el if dir_el is not None else "out"

        def _presence(parent: ET._Element | None) -> Optional[str]:
            if parent is None:
                return None
            return parent.findtext(f"{{{IPXACT_NS}}}presence")

        result: Dict[str, Any] = {
            "vlnv": {
                "vendor": root.findtext(f"{{{IPXACT_NS}}}vendor"),
                "library": root.findtext(f"{{{IPXACT_NS}}}library"),
                "name": root.findtext(f"{{{IPXACT_NS}}}name"),
                "version": root.findtext(f"{{{IPXACT_NS}}}version"),
            },
            "busType": {},
            "ports": {},
        }
        bus_type = root.find(f"{{{IPXACT_NS}}}busType")
        if bus_type is not None:
            result["busType"] = {
                k: bus_type.get(k) for k in ("vendor", "library", "name", "version")
            }
        for port in root.xpath("./ipxact:ports/ipxact:port", namespaces={"ipxact": IPXACT_NS}):
            name = port.findtext(f"{{{IPXACT_NS}}}logicalName")
            wire = port.find(f"{{{IPXACT_NS}}}wire")
            on_init = wire.find(f"{{{IPXACT_NS}}}onInitiator") if wire is not None else None
            on_target = wire.find(f"{{{IPXACT_NS}}}onTarget") if wire is not None else None
            result["ports"][name] = {
                "presence_initiator": _presence(on_init),
                "direction_initiator": _direction(on_init),
                "presence_target": _presence(on_target),
                "direction_target": _direction(on_target),
            }
        return result

    @staticmethod
    def get_bus_definition(root: ET._Element) -> Dict[str, Any]:
        return {
            "vlnv": {
                "vendor": root.findtext(f"{{{IPXACT_NS}}}vendor"),
                "library": root.findtext(f"{{{IPXACT_NS}}}library"),
                "name": root.findtext(f"{{{IPXACT_NS}}}name"),
                "version": root.findtext(f"{{{IPXACT_NS}}}version"),
            },
        }

    @staticmethod
    def _collect_iface_defs(
        top_ir: Module,
    ) -> Tuple[Dict[str, ET._Element], Dict[str, ET._Element]]:
        back = IPXACTBackend()
        repr = back.represent(top_ir)
        absdefs: Dict[str, ET._Element] = {}
        busdefs: Dict[str, ET._Element] = {}
        for out in back.serialize(repr):
            et = ET.fromstring(out.content)
            tag = ET.QName(et).localname
            if tag == "abstractionDefinition":
                absdefs[et.findtext(f"{{{IPXACT_NS}}}name")] = et
            elif tag == "busDefinition":
                busdefs[et.findtext(f"{{{IPXACT_NS}}}name")] = et
        return absdefs, busdefs

    @pytest.mark.parametrize(
        "top, golden_paths",
        [
            (
                intf_top,
                [
                    (
                        Path("examples/ir_examples/interface/ipxact/amba.com/AMBA4/axi4stream.xml"),
                        None,
                    ),
                ],
            ),
            (
                intr_top,
                [
                    (
                        Path(
                            "examples/ir_examples/interconnect/ipxact/"
                            "antmicro.com/interconnect/interface/wishbone_b4_def.xml"
                        ),
                        Path(
                            "examples/ir_examples/interconnect/ipxact/"
                            "antmicro.com/interconnect/interface/wishbone_b4.xml"
                        ),
                    ),
                ],
            ),
        ],
    )
    def test_ir_examples_iface_defs_xmldiffa(
        self,
        top: Module,
        golden_paths: List[Tuple[Optional[Path], Optional[Path]]],
    ):
        absdefs, busdefs = TestIpxactIrExamples._collect_iface_defs(top)

        def filterFunc(value: Any) -> bool:
            return all(
                predicate(value)
                for predicate in [
                    TestIpxactIrExamples.filter_empty_strings,
                    TestIpxactIrExamples.filter_schema_location,
                    TestIpxactIrExamples.filter_abs_def_ports,
                    TestIpxactIrExamples.filter_bus_def_extras,
                ]
            )

        for absdef_path, busdef_path in golden_paths:
            if absdef_path is not None:
                golden_abs = ET.parse(absdef_path)
                abs_name = golden_abs.findtext(f"{{{IPXACT_NS}}}name")
                assert abs_name in absdefs, f"no absDef '{abs_name}' in output"
                diff = xmldiff.diff_trees(absdefs[abs_name], golden_abs)
                diff_filtered = list(filter(filterFunc, diff))
                assert not diff_filtered, "\n".join(str(d) for d in diff_filtered)

            if busdef_path is not None:
                golden_bus = ET.parse(busdef_path)
                bus_name = golden_bus.findtext(f"{{{IPXACT_NS}}}name")
                assert bus_name in busdefs, f"no busDef '{bus_name}' in output"
                diff = xmldiff.diff_trees(busdefs[bus_name], golden_bus)
                diff_filtered = list(filter(filterFunc, diff))
                assert not diff_filtered, "\n".join(str(d) for d in diff_filtered)

    @pytest.mark.parametrize(
        "top, golden_paths",
        [
            (
                intf_top,
                [
                    (
                        Path("examples/ir_examples/interface/ipxact/amba.com/AMBA4/axi4stream.xml"),
                        None,
                    ),
                ],
            ),
            (
                intr_top,
                [
                    (
                        Path(
                            "examples/ir_examples/interconnect/ipxact/"
                            "antmicro.com/interconnect/interface/wishbone_b4_def.xml"
                        ),
                        Path(
                            "examples/ir_examples/interconnect/ipxact/"
                            "antmicro.com/interconnect/interface/wishbone_b4.xml"
                        ),
                    ),
                ],
            ),
        ],
    )
    def test_ir_examples_iface_defs_semantic(
        self,
        top: Module,
        golden_paths: List[Tuple[Optional[Path], Optional[Path]]],
    ):
        absdefs, busdefs = TestIpxactIrExamples._collect_iface_defs(top)

        for absdef_path, busdef_path in golden_paths:
            if absdef_path is not None:
                golden_abs = ET.parse(absdef_path)
                abs_name = golden_abs.findtext(f"{{{IPXACT_NS}}}name")
                output_abs = TestIpxactIrExamples.get_abstraction_definition(absdefs[abs_name])
                golden_struct = TestIpxactIrExamples.get_abstraction_definition(golden_abs)
                assert output_abs["vlnv"] == golden_struct["vlnv"]
                assert output_abs["busType"] == golden_struct["busType"]
                for port_name, output_port in output_abs["ports"].items():
                    assert port_name in golden_struct["ports"], (
                        f"port '{port_name}' not in golden absDef"
                    )
                    assert output_port == golden_struct["ports"][port_name], (
                        f"port '{port_name}' mismatch: {output_port} vs "
                        f"{golden_struct['ports'][port_name]}"
                    )

            if busdef_path is not None:
                golden_bus = ET.parse(busdef_path)
                bus_name = golden_bus.findtext(f"{{{IPXACT_NS}}}name")
                output_bus = TestIpxactIrExamples.get_bus_definition(busdefs[bus_name])
                golden_bus_struct = TestIpxactIrExamples.get_bus_definition(golden_bus)
                assert output_bus == golden_bus_struct
