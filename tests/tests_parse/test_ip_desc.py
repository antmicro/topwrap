# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import tempfile
from collections import defaultdict
from collections.abc import Mapping

import pytest
import yaml
from deepdiff import DeepDiff
from marshmallow import ValidationError

from topwrap.interface import InterfaceMode
from topwrap.interface_grouper import standard_iface_grouper
from topwrap.ip_desc import (
    IPCoreDescription,
    IPCoreInterface,
    IPCoreIntfPorts,
    IPCoreParameter,
    IPCorePorts,
)
from topwrap.verilog_parser import VerilogModule


class TestIPCoreDescription:
    @pytest.fixture
    def invalid_interface_type_core(self):
        return yaml.safe_load(
            r"""
name: test_ip
interfaces:
    intf1:
        mode: INVALID
        type: IDONTEXIST"""
        )

    @pytest.fixture
    def invalid_interface_compliance_core(self):
        return yaml.safe_load(
            r"""
name: test_ip
interfaces:
    i1:
        mode: slave
        type: AXI4Stream
        signals:
            out:
                TDATA: [p1]
                TVALID: [p2]
                TBUBU: [p3]
            in:
                TREADY: [p4]"""
        )

    @pytest.fixture
    def optional_missing_interface_compliance_core(self):
        return yaml.safe_load(
            r"""
name: test_ip
interfaces:
    i1:
        mode: slave
        type: AXI4Stream
        signals:
            out:
                TDATA: [p1]
                TVALID: [p2]
                TLAST: [p3]
            in:
                TREADY: [p4]"""
        )

    @pytest.fixture
    def completely_invalid_core(self):
        with open("tests/data/data_parse/ip_core_invalid.yaml") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def completely_valid_core(self):
        with open("tests/data/data_parse/ip_core_valid.yaml") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def ip_core_description(self, axi_verilog_module: VerilogModule) -> IPCoreDescription:
        return axi_verilog_module.to_ip_core_description(standard_iface_grouper())

    @pytest.fixture
    def expected_output(self) -> IPCoreDescription:
        return IPCoreDescription.load("tests/data/data_parse/axi_axil_adapter.yaml", False)

    @pytest.fixture
    def force_compliance(self):
        from topwrap.config import config

        org = config.force_interface_compliance
        config.force_interface_compliance = True
        yield
        config.force_interface_compliance = org

    def test_conversion_from_hdl_module(
        self, ip_core_description: IPCoreDescription, expected_output: IPCoreDescription
    ):
        assert DeepDiff(expected_output, ip_core_description) == {}

    def test_invalid_interface_type(self, invalid_interface_type_core):
        with pytest.raises(
            ValidationError, match="'Invalid interface type: IDONTEXIST'"
        ) and pytest.raises(ValidationError, match="'Must be one of: master,"):
            IPCoreDescription.Schema().load(invalid_interface_type_core)

    def test_invalid_interface_compliance(
        self, invalid_interface_compliance_core, force_compliance
    ):
        with pytest.raises(
            ValidationError, match='Required out port "TLAST" of interface "AXI4Stream" not present'
        ) and pytest.raises(
            ValidationError, match='Unknown out port "TBUBU", not present in interface "AXI4Stream"'
        ):
            IPCoreDescription.Schema().load(invalid_interface_compliance_core)

    def test_optional_signal_missing_compliance(
        self, optional_missing_interface_compliance_core, force_compliance
    ):
        IPCoreDescription.Schema().load(optional_missing_interface_compliance_core)

    def test_interface_compliance_off(self, invalid_interface_compliance_core):
        IPCoreDescription.Schema().load(invalid_interface_compliance_core)

    def test_builtins_presence(self):
        for ip in (
            "axi_axil_adapter",
            "axi_interconnect",
            "axi_protocol_converter",
            "axis_async_fifo",
            "axis_dwidth_converter",
        ):
            assert ip in IPCoreDescription.get_builtins(), f'Builtin IP "{ip}" is missing'

    def test_builtins_compliance(self, force_compliance):
        IPCoreDescription.get_builtins.cache_clear()
        IPCoreDescription.get_builtins()

    def test_load_fallback(self):
        with pytest.raises(FileNotFoundError):
            IPCoreDescription.load("axi_interconnect.yaml", False)

        IPCoreDescription.load("axi_interconnect.yaml")

    def test_save(self, expected_output: IPCoreDescription):
        with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
            expected_output.save(f.name)
            loaded = IPCoreDescription.load(f.name, False)
            assert DeepDiff(expected_output, loaded) == {}

    def test_invalid_syntax(self, completely_invalid_core):
        EXPECTED = {
            "name": ["Not a valid string."],
            "signals": {
                "in": {
                    1: [
                        {"_schema": ["Not a valid string."]},
                        {"_schema": ["Length must be 1."]},
                        {"_schema": ["Length must be 3."]},
                        {"_schema": ["Length must be 5."]},
                    ],
                    2: [
                        {"_schema": ["Not a valid string."]},
                        {"_schema": ["Length must be 1."]},
                        {"_schema": ["Length must be 3."]},
                        {"_schema": ["Length must be 5."]},
                    ],
                    3: [
                        {"_schema": ["Not a valid string."]},
                        {"_schema": ["Not a valid tuple."]},
                        {"_schema": ["Not a valid tuple."]},
                        {"_schema": ["Not a valid tuple."]},
                    ],
                },
                "inout": ["Field may not be null."],
                "outbar": ["Unknown field."],
            },
            "parameters": {
                "param": {
                    "value": [
                        {"_schema": ["Not a valid integer."]},
                        {"_schema": ["Not a valid string."]},
                        {
                            "width": ["Missing data for required field."],
                            "value": ["Missing data for required field."],
                        },
                    ]
                },
                "param2": {
                    "value": [
                        {"_schema": ["Not a valid integer."]},
                        {"_schema": ["Not a valid string."]},
                        {"_schema": ["Invalid input type."]},
                    ]
                },
                "param5": {
                    "value": [
                        {"_schema": ["Not a valid integer."]},
                        {"_schema": ["Not a valid string."]},
                        {
                            "width": ["Not a valid integer."],
                            "value": [
                                {"_schema": ["Not a valid integer."]},
                                {"_schema": ["Not a valid string."]},
                            ],
                        },
                    ]
                },
            },
            "interfaces": {
                "foo_bar_adapter": {
                    "value": {
                        "type": ["Not a valid string."],
                        "mode": ["Must be one of: master, slave, unspecified."],
                        "signals": {
                            "out": {
                                "ABC": {
                                    "value": [
                                        {"_schema": ["Not a valid string."]},
                                        {"_schema": ["Length must be 1."]},
                                        {"_schema": ["Length must be 3."]},
                                        {"_schema": ["Length must be 5."]},
                                    ]
                                }
                            },
                            "barfoo": ["Unknown field."],
                            "foobar": ["Unknown field."],
                        },
                    }
                }
            },
            "invalid": ["Unknown field."],
        }

        def deep_normalize(err):
            norm = err
            if isinstance(err, ValidationError):
                norm = err.normalized_messages()
            if isinstance(norm, defaultdict):
                norm = dict(norm)
            if isinstance(norm, Mapping):
                for key in norm:
                    norm[key] = deep_normalize(norm[key])
            elif isinstance(norm, list):
                for i in range(len(norm)):
                    norm[i] = deep_normalize(norm[i])
            return norm

        try:
            IPCoreDescription.Schema().load(completely_invalid_core)
        except ValidationError as e:
            assert DeepDiff(deep_normalize(e), deep_normalize(EXPECTED)) == {}

    def test_valid_syntax(self, completely_valid_core, force_compliance):
        ip: IPCoreDescription = IPCoreDescription.Schema().load(completely_valid_core)

        assert ip == IPCoreDescription(
            name="correct_core",
            signals=IPCorePorts(
                input={
                    "clk",
                    ("btns", 32, 0, 15, 10),
                    ("leds", 10, 0),
                    ("rst",),
                    ("useless", 22, 10),
                },
                output=set(),
                inout=set(),
            ),
            parameters={
                "p1": 3,
                "p2": "p1+4",
                "p3": IPCoreParameter(width=4, value=5),
                "p4": IPCoreParameter(width=4, value="p2"),
            },
            interfaces={
                "intf1": IPCoreInterface(
                    type="wishbone",
                    mode=InterfaceMode.MASTER,
                    signals=IPCoreIntfPorts(
                        input={"ack": ("ack", 2, 0)},
                        output={"cyc": "cyc", "stb": ("cyc", 3, 0, 1, 0)},
                        inout={},
                    ),
                )
            },
        )
