# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from uuid import uuid4

import pytest

from examples.ir_examples.modules import inv_top
from tests.update_test_data import (
    _check_generated_files,
    _check_yaml_files,
    _normalize_dataflow,
    _normalize_yaml,
)
from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.common import InverterMetanode


def _dataflow():
    def node(name):
        return {
            "id": str(uuid4()),
            "name": "Block",
            "instanceName": name,
            "properties": [],
            "interfaces": [{"id": str(uuid4()), "name": "port", "direction": "inout"}],
        }

    nodes = [node(name) for name in ("source", "sink", "other")]
    graph = {
        "id": str(uuid4()),
        "name": "top",
        "nodes": nodes,
        "connections": [
            {
                "id": str(uuid4()),
                "from": nodes[0]["interfaces"][0]["id"],
                "to": nodes[1]["interfaces"][0]["id"],
            }
        ],
    }
    return {"graphs": [graph], "entryGraph": graph["id"]}


def test_dataflow_ignores_generated_ids_and_entity_order():
    first, second = _dataflow(), _dataflow()
    second["graphs"][0]["nodes"].reverse()
    assert _normalize_dataflow(first) == _normalize_dataflow(second)


def test_dataflow_detects_rewired_connection():
    original = _dataflow()
    changed = deepcopy(original)
    graph = changed["graphs"][0]
    graph["connections"][0]["to"] = graph["nodes"][2]["interfaces"][0]["id"]
    assert _normalize_dataflow(original) != _normalize_dataflow(changed)


@pytest.mark.parametrize(("direction", "equivalent"), [("inout", True), ("output", False)])
def test_dataflow_handles_reversed_connection(direction, equivalent):
    original = _dataflow()
    original["graphs"][0]["nodes"][0]["interfaces"][0]["direction"] = direction
    changed = deepcopy(original)
    connection = changed["graphs"][0]["connections"][0]
    connection["from"], connection["to"] = connection["to"], connection["from"]
    assert (_normalize_dataflow(original) == _normalize_dataflow(changed)) is equivalent


def test_dataflow_normalizes_generated_inverters_by_wiring():
    first = KpmBackend(depth=-1).represent(inv_top).dataflow
    second = KpmBackend(depth=-1).represent(inv_top).dataflow
    second["graphs"][0]["nodes"].reverse()
    assert _normalize_dataflow(first) == _normalize_dataflow(second)

    graph = second["graphs"][0]
    inverter_ports = {
        port["id"]
        for node in graph["nodes"]
        if node["name"] == InverterMetanode.name
        for port in node["interfaces"]
    }
    inputs = [conn for conn in graph["connections"] if conn["to"] in inverter_ports]
    first_input = inputs[0]
    other_input = next(conn for conn in inputs[1:] if conn["from"] != first_input["from"])
    first_input["from"], other_input["from"] = other_input["from"], first_input["from"]
    assert _normalize_dataflow(first) != _normalize_dataflow(second)


def test_dataflow_rejects_duplicate_interface_id():
    data = _dataflow()
    nodes = data["graphs"][0]["nodes"]
    nodes[2]["interfaces"][0]["id"] = nodes[0]["interfaces"][0]["id"]
    nodes.reverse()
    with pytest.raises(ValueError, match="Duplicate dataflow ID"):
        _normalize_dataflow(data)


def test_dataflow_preserves_uuid_property_values():
    original = _dataflow()
    original["graphs"][0]["nodes"][0]["properties"] = [
        {"id": str(uuid4()), "name": "value", "value": str(uuid4())}
    ]
    changed = deepcopy(original)
    changed["graphs"][0]["nodes"][0]["properties"][0]["value"] = str(uuid4())
    assert _normalize_dataflow(original) != _normalize_dataflow(changed)


def test_dataflow_detects_changed_entry_graph():
    original = _dataflow()
    child = _dataflow()["graphs"][0]
    child["name"] = "child"
    original["graphs"].append(child)
    changed = deepcopy(original)
    changed["entryGraph"] = child["id"]
    assert _normalize_dataflow(original) != _normalize_dataflow(changed)


@pytest.mark.parametrize("field", ["bound", "members"])
def test_yaml_preserves_ordered_lists(field):
    assert _normalize_yaml({field: [7, 0]}) != _normalize_yaml({field: [0, 7]})


def test_yaml_ignores_port_declaration_order():
    assert _normalize_yaml({"in": [{"name": "a"}, {"name": "b"}]}) == _normalize_yaml(
        {"in": [{"name": "b"}, {"name": "a"}]}
    )


def test_check_reports_missing_unexpected_and_outdated_files(tmp_path):
    missing, extra, stale = [tmp_path / name for name in ("missing", "extra", "stale")]
    extra.write_text("extra")
    stale.write_text("old")
    errors = _check_generated_files(
        {missing: "new", stale: "new"}, {extra, stale}, lambda path: path.read_text()
    )
    assert errors == [f"missing {missing}", f"unexpected {extra}", f"outdated {stale}"]


@pytest.mark.parametrize("value", [0, 0.0])
def test_check_detects_changed_scalar_type(tmp_path, value):
    fixture = tmp_path / "fixture"
    errors = _check_generated_files(
        {fixture: {"abstract": False}}, {fixture}, lambda _: {"abstract": value}
    )
    assert errors == [f"outdated {fixture}"]


def test_yaml_check_detects_changed_scalar_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fixture = tmp_path / "tests/data/data_yaml/ipcore/fixture.yaml"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("abstract: 0\n")
    relative = fixture.relative_to(tmp_path)
    assert _check_yaml_files({relative: "abstract: false\n"}) == [f"outdated {relative}"]
