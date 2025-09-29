# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
from typing import Dict, Union, cast

import pytest

from topwrap.frontend.kpm.frontend import KpmFrontend
from topwrap.frontend.yaml.ip_core import InterfaceDescriptionFrontend
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    PortConnection,
    PortDirection,
)
from topwrap.model.design import ModuleInstance
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module
from topwrap.util import JsonType, read_json_file


@pytest.fixture
def test_dirs() -> Dict[str, Path]:
    COMMON = "tests/data/data_kpm/"
    paths = {}
    for glob in (COMMON + "examples/*", COMMON + "conversions/*"):
        for path in Path(".").glob(glob):
            ip_name = path.stem
            paths[ip_name] = path
    return paths


@pytest.fixture
def all_specification_files(test_dirs: Dict[str, Path]) -> Dict[str, JsonType]:
    return {
        ip_name: read_json_file(dir / f"specification_{ip_name}.json")
        for ip_name, dir in test_dirs.items()
    }


@pytest.fixture
def all_dataflow_files(test_dirs: Dict[str, Path]) -> Dict[str, JsonType]:
    return {
        ip_name: read_json_file(dir / f"dataflow_{ip_name}.json")
        for ip_name, dir in test_dirs.items()
    }


@pytest.fixture
def all_design_modules(
    all_dataflow_files: Dict[str, JsonType], all_specification_files: Dict[str, JsonType]
) -> Dict[str, Module]:
    if_names = ["AXI4", "AXI3", "AXI4Lite", "AXI4Stream"]
    ifs = [InterfaceDescriptionFrontend.from_loaded(x) for x in if_names]
    frontend = KpmFrontend(interfaces=cast(list[InterfaceDefinition], ifs))

    designs = {}
    for name, dataflow in all_dataflow_files.items():
        designs[name] = frontend.parse_str(
            [json.dumps(all_specification_files[name]), json.dumps(dataflow)]
        ).modules[-1]

    return designs


def _all_inst_params(inst: ModuleInstance) -> dict[str, Union[str, None]]:
    params = {
        p.name: p.default_value.value if p.default_value else None for p in inst.module.parameters
    }
    params.update({p.resolve().name: v.value for p, v in inst.parameters.items()})

    return params


def _flatten_conns_to_dict(
    conns: Union[list[PortConnection], list[InterfaceConnection], list[ConstantConnection]],
) -> dict[tuple[str, ...], tuple[str, ...]]:
    out = {}

    for conn in conns:
        if isinstance(conn, ConstantConnection):
            target_name = (
                conn.target.instance.name if conn.target.instance else conn.target.io.parent.id.name
            )
            out.update({(target_name, conn.target.io.name): conn.source.value})
        else:
            source_name = (
                conn.source.instance.name if conn.source.instance else conn.source.io.parent.id.name
            )
            target_name = (
                conn.target.instance.name if conn.target.instance else conn.target.io.parent.id.name
            )
            source = conn.source.io
            target = conn.target.io

            # Order connections consistently
            if target_name > source_name:
                source, target = target, source
                source_name, target_name = target_name, source_name

            out.update({(target_name, target.name): (source_name, source.name)})

    return out


def _module_port_dict(module: Module) -> dict[str, tuple[PortDirection, str]]:
    return {port.name: (port.direction, port.type.size.value) for port in module.ports}


class TestKpmFrontendPWMExample:
    @pytest.fixture
    def pwm_module(self, all_design_modules: Dict[str, Module]) -> Module:
        return all_design_modules["pwm"]

    def test_properties(self, pwm_module: Module):
        """
        Check that the components have expected parameter values.
        """
        assert pwm_module.design

        axi_inst = pwm_module.design.components.find_by_name_or_error("axi_bridge")

        assert _all_inst_params(axi_inst) == {
            "ADDR_WIDTH": "32",
            "AXI_DATA_WIDTH": "32",
            "AXI_ID_WIDTH": "12",
            "AXI_STRB_WIDTH": "AXI_DATA_WIDTH/8",
            "AXIL_DATA_WIDTH": "32",
            "AXIL_STRB_WIDTH": "AXIL_DATA_WIDTH/8",
        }

    def test_externals(self, pwm_module: Module):
        """
        Check that the module has all expected external ports.
        """
        assert _module_port_dict(pwm_module) == {
            "pwm": (PortDirection.OUT, "1"),
        }

    def test_connections(self, pwm_module: Module):
        """
        Check that the design has all expected connections.
        """
        design = pwm_module.design
        assert design

        AXI_NAME = "axi_bridge"
        PS7_NAME = "ps7"
        PWM_NAME = "litex_pwm_top"

        port_conns = [x for x in design.connections if isinstance(x, PortConnection)]
        assert _flatten_conns_to_dict(port_conns) == {
            (PS7_NAME, "MAXIGP0ACLK"): (PS7_NAME, "FCLK0"),
            (AXI_NAME, "clk"): (PS7_NAME, "FCLK0"),
            (AXI_NAME, "rst"): (PS7_NAME, "FCLK_RESET0_N"),
            (PWM_NAME, "sys_clk"): (PS7_NAME, "FCLK0"),
            (PWM_NAME, "sys_rst"): (PS7_NAME, "FCLK_RESET0_N"),
            (PWM_NAME, "pwm"): ("top", "pwm"),
        }

        if_conns = [x for x in design.connections if isinstance(x, InterfaceConnection)]
        assert _flatten_conns_to_dict(if_conns) == {
            (AXI_NAME, "s_axi"): (PS7_NAME, "M_AXI_GP0"),
            (AXI_NAME, "m_axi"): (PWM_NAME, "s_axi"),
        }

        const_conns = [x for x in design.connections if isinstance(x, ConstantConnection)]
        assert len(const_conns) == 0

    def test_nodes(self, pwm_module: Module):
        """
        Check whether all expected nodes exist in the hierarchy.
        """

        hierarchy_names = [x.id.name for x in pwm_module.hierarchy()]
        assert sorted(hierarchy_names) == [
            "axi_axil_adapter",
            "litex_pwm",
            "ps7",
            "top",
        ]


class TestKpmFrontendHDMIExample:
    @pytest.fixture
    def hdmi_module(self, all_design_modules: Dict[str, Module]) -> Module:
        return all_design_modules["hdmi"]

    def test_properties(self, hdmi_module: Module):
        """
        Check that the components have expected parameter values.
        """
        assert hdmi_module.design

        axi_inst = hdmi_module.design.components.find_by_name_or_error("axi_interconnect0")

        params = _all_inst_params(axi_inst)
        assert params["ADDR_WIDTH"] == "32"
        assert params["M_ADDR_WIDTH"] == "96'd295147905248072302608"

    def test_externals(self, hdmi_module: Module):
        """
        Check that the module has all expected external ports.
        """
        assert _module_port_dict(hdmi_module) == {
            "HDMI_CLK_N": (PortDirection.OUT, "1"),
            "HDMI_CLK_P": (PortDirection.OUT, "1"),
            "HDMI_D0_N": (PortDirection.OUT, "1"),
            "HDMI_D0_P": (PortDirection.OUT, "1"),
            "HDMI_D1_N": (PortDirection.OUT, "1"),
            "HDMI_D1_P": (PortDirection.OUT, "1"),
            "HDMI_D2_N": (PortDirection.OUT, "1"),
            "HDMI_D2_P": (PortDirection.OUT, "1"),
            "ddr_addr": (PortDirection.INOUT, "1"),
            "ddr_bankaddr": (PortDirection.INOUT, "1"),
            "ddr_cas_n": (PortDirection.INOUT, "1"),
            "ddr_cke": (PortDirection.INOUT, "1"),
            "ddr_clk": (PortDirection.INOUT, "1"),
            "ddr_clk_n": (PortDirection.INOUT, "1"),
            "ddr_cs_n": (PortDirection.INOUT, "1"),
            "ddr_dm": (PortDirection.INOUT, "1"),
            "ddr_dq": (PortDirection.INOUT, "1"),
            "ddr_dqs": (PortDirection.INOUT, "1"),
            "ddr_dqs_n": (PortDirection.INOUT, "1"),
            "ddr_drstb": (PortDirection.INOUT, "1"),
            "ddr_odt": (PortDirection.INOUT, "1"),
            "ddr_ras_n": (PortDirection.INOUT, "1"),
            "ddr_vr_n": (PortDirection.INOUT, "1"),
            "ddr_vr": (PortDirection.INOUT, "1"),
            "ddr_web": (PortDirection.INOUT, "1"),
            "ps_mio": (PortDirection.INOUT, "1"),
            "ps_clk": (PortDirection.INOUT, "1"),
            "ps_porb": (PortDirection.INOUT, "1"),
            "ps_srstb": (PortDirection.INOUT, "1"),
        }

    def test_connections(self, hdmi_module: Module):
        """
        Check that the design has all expected connections.
        """
        design = hdmi_module.design
        assert design

        port_conns = [x for x in design.connections if isinstance(x, PortConnection)]
        # Too many to list here...
        assert len(port_conns) == 76

        if_conns = [x for x in design.connections if isinstance(x, InterfaceConnection)]
        assert _flatten_conns_to_dict(if_conns) == {
            ("axi_bridge_disp", "s_axi"): ("axi_interconnect0", "m_axi_2"),
            ("axi_bridge_dma", "s_axi"): ("axi_interconnect0", "m_axi_1"),
            ("axi_bridge_mmcm", "s_axi"): ("axi_interconnect0", "m_axi_0"),
            ("axi_interconnect0", "s_axi_0"): ("ps7", "M_AXI_GP0"),
            ("axi_protocol_converter0", "S_AXI"): ("dma", "m_axi"),
            ("axis_clock_converter", "s_axis"): ("dma", "m_axis"),
            ("axis_clock_converter", "m_axis"): ("axis_dwidth_converter", "s_axis"),
            ("axi_bridge_disp", "m_axi"): ("disp", "S00_AXI"),
            ("axis_dwidth_converter", "m_axis"): ("disp", "S_AXIS"),
            ("axi_bridge_dma", "m_axi"): ("dma", "s_axi"),
            ("axi_bridge_mmcm", "m_axi"): ("mmcm", "axi"),
            ("axi_protocol_converter0", "M_AXI"): ("ps7", "S_AXI_HP0"),
        }

        const_conns = [x for x in design.connections if isinstance(x, ConstantConnection)]
        assert _flatten_conns_to_dict(const_conns) == {
            ("reset0", "aux_reset_in"): "0",
            ("reset0", "dcm_locked"): "1",
            ("reset0", "ext_reset_in"): "0",
            ("reset0", "mb_debug_sys_rst"): "0",
            ("reset1", "aux_reset_in"): "0",
            ("reset1", "dcm_locked"): "1",
            ("reset1", "ext_reset_in"): "0",
            ("reset1", "mb_debug_sys_rst"): "0",
        }

    def test_nodes(self, hdmi_module: Module):
        """
        Check whether all expected nodes exist in the hierarchy.
        """

        hierarchy_names = [x.id.name for x in hdmi_module.hierarchy()]
        assert sorted(hierarchy_names) == [
            "axi_axil_adapter",
            "axi_dispctrl",
            "axi_interconnect",
            "axi_protocol_converter",
            "axis_async_fifo",
            "axis_dwidth_converter",
            "clock_crossing",
            "dma_axi_in_axis_out",
            "hdmi_tx",
            "litex_mmcm",
            "proc_sys_reset",
            "ps7",
            "top",
        ]


class TestKpmFrontendHierarchyExample:
    @pytest.fixture
    def hierarchy_module(self, all_design_modules: Dict[str, Module]) -> Module:
        return all_design_modules["hierarchy"]

    @pytest.fixture
    def counter_module(self, hierarchy_module: Module) -> Module:
        assert hierarchy_module.design
        counter_inst = hierarchy_module.design.components.find_by_name_or_error("counter")
        return counter_inst.module

    @pytest.fixture
    def complex_sub_module(self, hierarchy_module: Module) -> Module:
        assert hierarchy_module.design
        complex_sub_inst = hierarchy_module.design.components.find_by_name_or_error("complex_sub")
        return complex_sub_inst.module

    @pytest.fixture
    def sub_1_module(self, complex_sub_module: Module) -> Module:
        assert complex_sub_module.design
        sub_1_inst = complex_sub_module.design.components.find_by_name_or_error("sub_1")
        return sub_1_inst.module

    @pytest.fixture
    def sub_2_module(self, complex_sub_module: Module) -> Module:
        assert complex_sub_module.design
        sub_2_inst = complex_sub_module.design.components.find_by_name_or_error("sub_2")
        return sub_2_inst.module

    def test_properties(self, hierarchy_module: Module):
        """
        Check that the components have expected parameter values.
        """
        assert hierarchy_module.design

        counter_inst = hierarchy_module.design.components.find_by_name_or_error("counter")
        counter = counter_inst.module
        assert counter.design
        c_mod_1_inst = counter.design.components.find_by_name_or_error("c_mod_1")
        assert _all_inst_params(c_mod_1_inst) == {"MAX_VALUE": "16"}

        complex_sub_inst = hierarchy_module.design.components.find_by_name_or_error("complex_sub")
        complex_sub = complex_sub_inst.module
        assert complex_sub.design

        sub_1_inst = complex_sub.design.components.find_by_name_or_error("sub_1")
        sub_1 = sub_1_inst.module
        assert sub_1.design

        s1_mod_3_inst = sub_1.design.components.find_by_name_or_error("s1_mod_3")
        assert _all_inst_params(s1_mod_3_inst) == {"SUB_VALUE": "18"}

    def test_externals_top(self, hierarchy_module: Module):
        """
        Check that the top module has all expected external ports.
        """
        assert _module_port_dict(hierarchy_module) == {
            "ex_in_1": (PortDirection.OUT, "1"),
            "ex_out_1": (PortDirection.IN, "1"),
            "ex_out_2": (PortDirection.IN, "1"),
        }

    def test_externals_counter(self, counter_module: Module):
        """
        Check that the counter module has all expected external ports.
        """

        assert _module_port_dict(counter_module) == {
            "c_in_1": (PortDirection.IN, "1"),
            "c_in_2": (PortDirection.IN, "1"),
            "c_out_1": (PortDirection.OUT, "1"),
        }

    def test_externals_complex_sub(self, complex_sub_module: Module):
        """
        Check that the complex_sub module has all expected external ports.
        """

        assert _module_port_dict(complex_sub_module) == {
            "cs_in_1": (PortDirection.IN, "1"),
            "cs_out_1": (PortDirection.OUT, "1"),
            "cs_empty_port_in": (PortDirection.IN, "1"),
        }

    def test_externals_sub_1(self, sub_1_module: Module):
        """
        Check that the sub_1 module has all expected external ports.
        """

        assert _module_port_dict(sub_1_module) == {
            "cs_s1_int_const_in": (PortDirection.IN, "1"),
            "cs_s1_mod_in_1": (PortDirection.IN, "1"),
            "cs_s1_int_out_1": (PortDirection.OUT, "1"),
            "cs_s1_int_out_2": (PortDirection.OUT, "1"),
            "cs_s1_empty_in": (PortDirection.IN, "1"),
            "cs_s1_empty_out": (PortDirection.OUT, "1"),
        }

    def test_externals_sub_2(self, sub_2_module: Module):
        """
        Check that the sub_2 module has all expected external ports.
        """

        assert _module_port_dict(sub_2_module) == {
            "cs_s2_int_in_1": (PortDirection.IN, "1"),
            "cs_s2_int_in_2": (PortDirection.IN, "1"),
            "cs_s2_mod_out_1": (PortDirection.OUT, "1"),
        }

    def test_connections_top(self, hierarchy_module: Module):
        """
        Check that the top design has all expected connections.
        """
        design = hierarchy_module.design
        assert design

        port_conns = [x for x in design.connections if isinstance(x, PortConnection)]
        assert _flatten_conns_to_dict(port_conns) == {
            ("counter", "c_in_1"): ("top", "ex_out_1"),
            ("counter", "c_in_2"): ("top", "ex_out_2"),
            ("complex_sub", "cs_in_1"): ("counter", "c_out_1"),
            ("complex_sub", "cs_out_1"): ("top", "ex_in_1"),
        }

        if_conns = [x for x in design.connections if isinstance(x, InterfaceConnection)]
        assert len(if_conns) == 0

        const_conns = [x for x in design.connections if isinstance(x, ConstantConnection)]
        assert len(const_conns) == 0

    def test_connections_counter(self, counter_module: Module):
        """
        Check that the counter design has all expected connections.
        """
        design = counter_module.design
        assert design

        port_conns = [x for x in design.connections if isinstance(x, PortConnection)]
        assert _flatten_conns_to_dict(port_conns) == {
            ("c_mod_1", "c_mod_in_1"): ("counter", "c_in_1"),
            ("c_mod_2", "c_mod_in_2"): ("counter", "c_in_2"),
            ("c_mod_2", "c_int_out_2"): ("c_mod_3", "c_int_in_1"),
            ("c_mod_1", "c_int_out_1"): ("c_mod_3", "c_int_in_2"),
            ("c_mod_3", "c_mod_out_1"): ("counter", "c_out_1"),
        }

        if_conns = [x for x in design.connections if isinstance(x, InterfaceConnection)]
        assert len(if_conns) == 0

        const_conns = [x for x in design.connections if isinstance(x, ConstantConnection)]
        assert _flatten_conns_to_dict(const_conns) == {
            ("c_mod_3", "c_int_const_in"): "1",
        }

    def test_connections_complex_sub(self, complex_sub_module: Module):
        """
        Check that the complex_sub design has all expected connections.
        """
        design = complex_sub_module.design
        assert design

        port_conns = [x for x in design.connections if isinstance(x, PortConnection)]
        assert _flatten_conns_to_dict(port_conns) == {
            ("complex_sub", "cs_in_1"): ("sub_1", "cs_s1_mod_in_1"),
            ("sub_1", "cs_s1_int_out_1"): ("sub_2", "cs_s2_int_in_1"),
            ("sub_1", "cs_s1_int_out_2"): ("sub_2", "cs_s2_int_in_2"),
            ("complex_sub", "cs_out_1"): ("sub_2", "cs_s2_mod_out_1"),
        }

        if_conns = [x for x in design.connections if isinstance(x, InterfaceConnection)]
        assert len(if_conns) == 0

        const_conns = [x for x in design.connections if isinstance(x, ConstantConnection)]
        assert _flatten_conns_to_dict(const_conns) == {
            ("sub_1", "cs_s1_int_const_in"): "1",
        }

    def test_connections_sub_1(self, sub_1_module: Module):
        """
        Check that the sub_1 design has all expected connections.
        """
        design = sub_1_module.design
        assert design

        port_conns = [x for x in design.connections if isinstance(x, PortConnection)]
        assert _flatten_conns_to_dict(port_conns) == {
            ("s1_mod_1", "cs_s1_f_ext_const_in"): ("sub_1", "cs_s1_int_const_in"),
            ("s1_mod_1", "cs_s1_f_mod_in_1"): ("sub_1", "cs_s1_mod_in_1"),
            ("s1_mod_2", "cs_s1_f_int_out_1"): ("sub_1", "cs_s1_int_out_1"),
            ("s1_mod_1", "cs_s1_mint_out_1"): ("s1_mod_3", "cs_s1_mint_in_2"),
            ("s1_mod_3", "cs_s1_f_int_out_2"): ("sub_1", "cs_s1_int_out_2"),
        }

        if_conns = [x for x in design.connections if isinstance(x, InterfaceConnection)]
        assert len(if_conns) == 0

        const_conns = [x for x in design.connections if isinstance(x, ConstantConnection)]
        assert len(const_conns) == 0

    def test_connections_sub_2(self, sub_2_module: Module):
        """
        Check that the sub_2 design has all expected connections.
        """
        design = sub_2_module.design
        assert design

        port_conns = [x for x in design.connections if isinstance(x, PortConnection)]
        assert _flatten_conns_to_dict(port_conns) == {
            ("s2_mod_1", "cs_s2_f_int_in_1"): ("sub_2", "cs_s2_int_in_1"),
            ("s2_mod_1", "cs_s2_f_int_in_2"): ("sub_2", "cs_s2_int_in_2"),
            ("s2_mod_2", "cs_s2_f_mod_out_1"): ("sub_2", "cs_s2_mod_out_1"),
            ("s2_mod_1", "cs_s2_mint_out_1"): ("s2_mod_2", "cs_s2_mint_in_1"),
            ("s2_mod_1", "cs_s2_mint_out_2"): ("s2_mod_2", "cs_s2_mint_in_2"),
        }

        if_conns = [x for x in design.connections if isinstance(x, InterfaceConnection)]
        assert len(if_conns) == 0

        const_conns = [x for x in design.connections if isinstance(x, ConstantConnection)]
        assert len(const_conns) == 0

    def test_nodes(self, hierarchy_module: Module):
        """
        Check whether all expected nodes exist in the hierarchy.
        """

        hierarchy_names = [x.id.name for x in hierarchy_module.hierarchy()]
        assert sorted(hierarchy_names) == [
            "c_mod_1",
            "c_mod_2",
            "c_mod_3",
            "complex_sub",
            "counter",
            "s1_mod_1",
            "s1_mod_2",
            "s1_mod_3",
            "s2_mod_1",
            "s2_mod_2",
            "sub_1",
            "sub_2",
            "top",
        ]
