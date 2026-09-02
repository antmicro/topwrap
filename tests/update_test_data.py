# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping

import cyclopts
import yaml

from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.common import InverterMetanode
from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.backend.yaml.backend import IpCoreDescriptionBackend
from topwrap.backend.yaml.interface import InterfaceDefinitionDescriptionBackend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.util import JsonType, read_json_file, save_file_to_json

if __package__:
    from .tests_kpm.conftest import all_design_paths, test_dirs_data
else:
    from tests_kpm.conftest import all_design_paths, test_dirs_data

cli = cyclopts.App()


def check_up_to_date_func():
    errors = []
    errors.extend(_check_json_files(_generated_dataflows(), "dataflow_*.json", _normalize_dataflow))
    errors.extend(
        _check_json_files(_generated_specifications(), "specification_*.json", lambda data: data)
    )
    errors.extend(_check_yaml_files(_generated_ipcore_and_iface_files()))

    if errors:
        raise RuntimeError(
            "Generated test data is out of date:\n" + "\n".join(f"  - {error}" for error in errors)
        )


def _check_generated_files(
    generated_files: Mapping[Path, str | JsonType],
    actual_files: set[Path],
    read_file: Callable[[Path], str | JsonType],
) -> list[str]:
    errors = []
    expected_files = set(generated_files)

    for path in sorted(expected_files - actual_files):
        errors.append(f"missing {path}")
    for path in sorted(actual_files - expected_files):
        errors.append(f"unexpected {path}")

    for path in sorted(expected_files & actual_files):
        try:
            if json.dumps(read_file(path), sort_keys=True) != json.dumps(
                generated_files[path], sort_keys=True
            ):
                errors.append(f"outdated {path}")
        except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
            errors.append(f"could not read {path}: {error}")

    return errors


def _json_serialized(data: JsonType) -> JsonType:
    return json.loads(json.dumps(data))


def _normalize_dataflow(data: Any) -> Any:
    """Replace generated identifiers with semantic paths, preserving references."""
    identifiers = {}
    paths = set()
    inout_ids = set()

    def register(identifier: str, path: tuple, *, equivalent: bool = False):
        if identifier in identifiers:
            raise ValueError(f"Duplicate dataflow ID: {identifier}")
        canonical = json.dumps(path, sort_keys=True)
        if canonical in paths and not equivalent:
            raise ValueError(f"Ambiguous dataflow identity: {canonical}")
        paths.add(canonical)
        identifiers[identifier] = canonical

    def register_node(node: dict, path: tuple, *, equivalent: bool = False):
        register(node["id"], path, equivalent=equivalent)
        for interface in node["interfaces"]:
            interface_id = interface["id"]
            direction = interface.get("direction")
            if direction == "inout":
                inout_ids.add(interface_id)
            register(
                interface_id,
                (*path, "interface", interface["name"], direction),
                equivalent=equivalent,
            )

    for graph in data["graphs"]:
        graph_id = next(
            (
                {prop["name"]: prop["value"] for prop in node["properties"]}
                for node in graph["nodes"]
                if node["name"] == "Identifier"
            ),
            {"name": graph.get("name")},
        )
        graph_path = ("graph", graph_id)
        register(graph["id"], graph_path)
        inverters = []
        for node in graph["nodes"]:
            properties = {prop["name"]: prop["value"] for prop in node["properties"]}
            node_path = (*graph_path, "node", node["name"], node.get("instanceName"), properties)
            if node["name"] == InverterMetanode.name:
                inverters.append((node, node_path))
            else:
                register_node(node, node_path)

        # Generated inverters connect regular ports and share the same instance name.
        incoming = defaultdict(list)
        outgoing = defaultdict(list)
        for connection in graph["connections"]:
            source, target = connection["from"], connection["to"]
            incoming[target].append(source)
            outgoing[source].append(target)
        for node, node_path in inverters:
            wiring = tuple(
                (
                    interface["name"],
                    sorted(identifiers[peer] for peer in incoming[interface["id"]]),
                    sorted(identifiers[peer] for peer in outgoing[interface["id"]]),
                )
                for interface in sorted(node["interfaces"], key=lambda interface: interface["name"])
            )
            register_node(node, (*node_path, wiring), equivalent=True)

    collections = {"graphs", "nodes", "interfaces", "properties", "connections"}
    references = {"from", "to", "subgraph", "entryGraph"}

    def normalize(value: Any, field: str = "") -> Any:
        if isinstance(value, dict):
            normalized = {
                key: normalize(item, key)
                for key, item in value.items()
                if key != "id" or field not in collections
            }
            if (
                field == "connections"
                and value.get("from") in inout_ids
                and value.get("to") in inout_ids
            ):
                # The backend orders two INOUT endpoints by their generated IDs.
                normalized["from"], normalized["to"] = sorted(
                    (normalized["from"], normalized["to"])
                )
            return normalized
        if isinstance(value, list):
            items = [normalize(item, field) for item in value]
            return (
                sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
                if field in collections
                else items
            )
        if field in references and isinstance(value, str):
            return identifiers.get(value, value)
        return value

    return normalize(data)


def _check_json_files(
    generated_files: Mapping[Path, JsonType],
    pattern: str,
    normalize: Callable[[JsonType], JsonType],
) -> list[str]:
    test_dirs = test_dirs_data().values()
    actual_files = {path for test_dir in test_dirs for path in test_dir.glob(pattern)}
    normalized_generated_files = {
        path: normalize(_json_serialized(content)) for path, content in generated_files.items()
    }
    return _check_generated_files(
        normalized_generated_files,
        actual_files,
        lambda path: normalize(read_json_file(path)),
    )


def _normalize_yaml(data: Any, field: str = "") -> Any:
    """Ignore port declaration order, preserving bounds and struct member order."""
    if isinstance(data, dict):
        return {key: _normalize_yaml(value, key) for key, value in data.items()}
    if isinstance(data, list):
        items = [_normalize_yaml(value) for value in data]
        if field in {"in", "out", "inout"}:
            return sorted(items, key=lambda value: json.dumps(value, sort_keys=True))
        return items
    return data


def _check_yaml_files(generated_files: Mapping[Path, str]) -> list[str]:
    actual_files = {
        *Path("tests/data/data_yaml/ipcore").glob("*.yaml"),
        *Path("tests/data/data_yaml/ifaces").glob("*.yaml"),
    }
    # This handwritten fixture is not produced by the example generator.
    actual_files.discard(Path("tests/data/data_yaml/ipcore/inout.yaml"))
    generated_yaml = {
        path: yaml.safe_dump(_normalize_yaml(yaml.safe_load(content)))
        for path, content in generated_files.items()
    }
    return _check_generated_files(
        generated_yaml,
        actual_files,
        lambda path: yaml.safe_dump(_normalize_yaml(yaml.safe_load(path.read_text()))),
    )


def _generated_dataflows() -> dict[Path, JsonType]:
    generated_files = {}
    test_dirs = test_dirs_data()
    for example_name, design in all_design_paths().items():
        frontend = YamlFrontend()
        out = frontend.parse_files([design])
        design_module = out.modules[0]
        design_module.design.update_interconnects_from_memory_maps()

        backend = KpmBackend(depth=-1)
        representation = backend.represent(design_module)
        generated_files[test_dirs[example_name] / f"dataflow_{example_name}.json"] = (
            representation.dataflow
        )
    return generated_files


def update_dataflows():
    generated_files = _generated_dataflows()
    for path, dataflow in generated_files.items():
        save_file_to_json(
            path.parent,
            path.name,
            dataflow,
        )


def _generated_specifications() -> dict[Path, JsonType]:
    generated_files = {}
    test_dirs = test_dirs_data()
    for example_name, design in all_design_paths().items():
        frontend = YamlFrontend()
        out = frontend.parse_files([design])
        design_module = out.modules[0]
        design_module.design.update_interconnects_from_memory_maps()

        spec = KpmSpecificationBackend.default()
        spec.add_module(design_module, recursive=True)
        spec = spec.build()

        generated_files[test_dirs[example_name] / f"specification_{example_name}.json"] = spec
    return generated_files


def update_specifications():
    generated_files = _generated_specifications()
    for path, specification in generated_files.items():
        save_file_to_json(path.parent, path.name, specification)


def _generated_ipcore_and_iface_files() -> dict[Path, str]:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.dirname(SCRIPT_DIR))
    from examples.ir_examples.modules import (
        adv_top,
        hier_top,
        intf_top,
        intr_top,
        inv_top,
        simp_top,
    )

    ip_core_dir = Path("tests/data/data_yaml/ipcore")
    ifaces_dir = Path("tests/data/data_yaml/ifaces")
    generated_files = {}

    irs = [
        adv_top,
        hier_top,
        intf_top,
        intr_top,
        inv_top,
        simp_top,
    ]
    for ir in irs:
        for iface in ir.interfaces:
            definition = iface.definition
            desc = InterfaceDefinitionDescriptionBackend().represent(definition)
            generated_files[ifaces_dir / f"{definition.id.combined()}.yaml"] = desc.to_yaml()
        backend = IpCoreDescriptionBackend()
        representation = backend.represent(ir)
        files = backend.serialize(representation)
        ip_core = next(files)
        generated_files[ip_core_dir / f"{ir.id.name}.yaml"] = ip_core.content
    return generated_files


def update_json_ipcore_iface():
    generated_files = _generated_ipcore_and_iface_files()
    for path, content in generated_files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


@cli.default
def update_test_data(
    *,
    dataflow: bool = False,
    specification: bool = False,
    ipcore_and_iface_json: bool = False,
    check_up_to_date: bool = False,
):
    if dataflow:
        update_dataflows()

    if specification:
        update_specifications()

    if ipcore_and_iface_json:
        update_json_ipcore_iface()

    if check_up_to_date:
        try:
            check_up_to_date_func()
        except RuntimeError as e:
            print(e)
            exit(1)


if __name__ == "__main__":
    cli()
