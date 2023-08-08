# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import pytest
from yaml import Loader, load


@pytest.fixture
def specification_schema_path() -> Path:
    specification_schema_path = "kenning-pipeline-manager/pipeline_manager/resources/schemas/unresolved_specification_schema.json"  # noqa: E501
    return Path(specification_schema_path)


@pytest.fixture
def specification_schema(specification_schema_path) -> dict:
    with open(specification_schema_path, "r") as f:
        specification_schema = json.load(f)
    return specification_schema


@pytest.fixture
def pwm_design_yaml() -> dict:
    with open("examples/pwm/project.yml", "r") as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def hdmi_design_yaml() -> dict:
    with open("examples/hdmi/project.yml", "r") as yamlfile:
        design = load(yamlfile, Loader=Loader)
    return design


@pytest.fixture
def pwm_ipcores_yamls() -> list:
    return [
        "fpga_topwrap/ips/axi/axi_axil_adapter.yaml",
        "examples/pwm/ipcores/ps7.yaml",
        "examples/pwm/ipcores/litex_pwm.yml",
    ]


@pytest.fixture
def hdmi_ipcores_yamls() -> list:
    _hdmi_yamls_prefix = "examples/hdmi/ipcores/"
    _axi_yamls_prefix = "fpga_topwrap/ips/axi/"
    return [
        _hdmi_yamls_prefix + "axi_dispctrl.yaml",
        _hdmi_yamls_prefix + "clock_crossing.yaml",
        _hdmi_yamls_prefix + "dma_axi_in_axis_out.yaml",
        _hdmi_yamls_prefix + "hdmi_tx.yaml",
        _hdmi_yamls_prefix + "litex_mmcm.yaml",
        _hdmi_yamls_prefix + "proc_sys_reset.yaml",
        _hdmi_yamls_prefix + "ps7.yaml",
        _axi_yamls_prefix + "axi_axil_adapter.yaml",
        _axi_yamls_prefix + "axi_interconnect.yaml",
        _axi_yamls_prefix + "axi_protocol_converter.yaml",
        _axi_yamls_prefix + "axis_dwidth_converter.yaml",
        _axi_yamls_prefix + "axis_async_fifo.yaml",
    ]


@pytest.fixture
def pwm_dataflow() -> dict:
    return {
        "graph": {
            "id": "169148525824333",
            "nodes": [
                {
                    "type": "litex_pwm",
                    "id": "node_16914852582434",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "sys_clk",
                            "id": "ni_16914852582430",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "sys_rst",
                            "id": "ni_16914852582431",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axi",
                            "id": "ni_16914852582433",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "pwm",
                            "id": "ni_16914852582432",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "litex_pwm_top",
                },
                {
                    "type": "axi_axil_adapter",
                    "id": "node_169148525824315",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "clk",
                            "id": "ni_169148525824311",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "rst",
                            "id": "ni_169148525824312",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axi",
                            "id": "ni_169148525824313",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "m_axi",
                            "id": "ni_169148525824314",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [
                        {"name": "ADDR_WIDTH", "id": "16914852582435", "value": "32"},
                        {"name": "AXI_DATA_WIDTH", "id": "16914852582436", "value": "32"},
                        {"name": "AXI_ID_WIDTH", "id": "16914852582437", "value": "12"},
                        {
                            "name": "AXI_STRB_WIDTH",
                            "id": "16914852582438",
                            "value": "AXI_DATA_WIDTH/8",
                        },
                        {"name": "AXIL_DATA_WIDTH", "id": "16914852582439", "value": "32"},
                        {
                            "name": "AXIL_STRB_WIDTH",
                            "id": "169148525824310",
                            "value": "AXIL_DATA_WIDTH/8",
                        },
                    ],
                    "name": "axi_bridge",
                },
                {
                    "type": "ps7",
                    "id": "node_169148525824321",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "MAXIGP0ACLK",
                            "id": "ni_169148525824316",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "FCLK0",
                            "id": "ni_169148525824317",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "MAXIGP0ARESETN",
                            "id": "ni_169148525824318",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "FCLK_RESET0_N",
                            "id": "ni_169148525824319",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "M_AXI_GP0",
                            "id": "ni_169148525824320",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "ps7",
                },
                {
                    "type": "External Output",
                    "id": "node_169148525824324",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_169148525824323",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "169148525824322", "value": "pwm"}
                    ],
                    "name": "External Output",
                },
            ],
            "connections": [
                {"id": "169148525824325", "from": "ni_169148525824317", "to": "ni_169148525824316"},
                {"id": "169148525824326", "from": "ni_169148525824317", "to": "ni_169148525824311"},
                {"id": "169148525824327", "from": "ni_169148525824319", "to": "ni_169148525824312"},
                {"id": "169148525824328", "from": "ni_169148525824317", "to": "ni_16914852582430"},
                {"id": "169148525824329", "from": "ni_169148525824319", "to": "ni_16914852582431"},
                {"id": "169148525824330", "from": "ni_169148525824320", "to": "ni_169148525824313"},
                {"id": "169148525824331", "from": "ni_169148525824314", "to": "ni_16914852582433"},
                {"id": "169148525824332", "from": "ni_16914852582432", "to": "ni_169148525824323"},
            ],
            "panning": {"x": 1500, "y": 405},
            "scaling": 0.6836922975942521,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }


@pytest.fixture
def hdmi_dataflow() -> dict:
    return {
        "graph": {
            "id": "1691485388185295",
            "nodes": [
                {
                    "type": "dma_axi_in_axis_out",
                    "id": "node_16914853881859",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "clock",
                            "id": "ni_16914853881850",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "reset",
                            "id": "ni_16914853881851",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "io_sync_readerSync",
                            "id": "ni_16914853881852",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "io_sync_writerSync",
                            "id": "ni_16914853881853",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axi",
                            "id": "ni_16914853881856",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "io_irq_readerDone",
                            "id": "ni_16914853881854",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "io_irq_writerDone",
                            "id": "ni_16914853881855",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_axis",
                            "id": "ni_16914853881857",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_axi",
                            "id": "ni_16914853881858",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "dma",
                },
                {
                    "type": "axi_dispctrl",
                    "id": "node_169148538818526",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "S_AXIS_ACLK",
                            "id": "ni_169148538818510",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "LOCKED_I",
                            "id": "ni_169148538818511",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s00_axi_aclk",
                            "id": "ni_169148538818512",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s00_axi_aresetn",
                            "id": "ni_169148538818513",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "S00_AXI",
                            "id": "ni_169148538818524",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "S_AXIS",
                            "id": "ni_169148538818525",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "FSYNC_O",
                            "id": "ni_169148538818514",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HSYNC_O",
                            "id": "ni_169148538818515",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "VSYNC_O",
                            "id": "ni_169148538818516",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "DE_O",
                            "id": "ni_169148538818517",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "DATA_O",
                            "id": "ni_169148538818518",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "CTL_O",
                            "id": "ni_169148538818519",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "VGUARD_O",
                            "id": "ni_169148538818520",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "DGUARD_O",
                            "id": "ni_169148538818521",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "DIEN_O",
                            "id": "ni_169148538818522",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "DIH_O",
                            "id": "ni_169148538818523",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "disp",
                },
                {
                    "type": "hdmi_tx",
                    "id": "node_169148538818547",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "PXLCLK_I",
                            "id": "ni_169148538818527",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "PXLCLK_5X_I",
                            "id": "ni_169148538818528",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "LOCKED_I",
                            "id": "ni_169148538818529",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "VGA_HS",
                            "id": "ni_169148538818530",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "VGA_VS",
                            "id": "ni_169148538818531",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "VGA_DE",
                            "id": "ni_169148538818532",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "DATA_I",
                            "id": "ni_169148538818533",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "CTL",
                            "id": "ni_169148538818534",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "VGUARD",
                            "id": "ni_169148538818535",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "DGUARD",
                            "id": "ni_169148538818536",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "DIEN",
                            "id": "ni_169148538818537",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "DIH",
                            "id": "ni_169148538818538",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "HDMI_CLK_P",
                            "id": "ni_169148538818539",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HDMI_CLK_N",
                            "id": "ni_169148538818540",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HDMI_D2_P",
                            "id": "ni_169148538818541",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HDMI_D2_N",
                            "id": "ni_169148538818542",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HDMI_D1_P",
                            "id": "ni_169148538818543",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HDMI_D1_N",
                            "id": "ni_169148538818544",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HDMI_D0_P",
                            "id": "ni_169148538818545",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "HDMI_D0_N",
                            "id": "ni_169148538818546",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "hdmi",
                },
                {
                    "type": "litex_mmcm",
                    "id": "node_169148538818555",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "sys_clk",
                            "id": "ni_169148538818548",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "sys_rst",
                            "id": "ni_169148538818549",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "clkgen_ref",
                            "id": "ni_169148538818550",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "axi",
                            "id": "ni_169148538818554",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "clkgen_out0",
                            "id": "ni_169148538818551",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "clkgen_out1",
                            "id": "ni_169148538818552",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "clkgen_locked",
                            "id": "ni_169148538818553",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "mmcm",
                },
                {
                    "type": "axi_interconnect",
                    "id": "node_169148538818575",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "clk",
                            "id": "ni_169148538818569",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "rst",
                            "id": "ni_169148538818570",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axi_0",
                            "id": "ni_169148538818571",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "m_axi_0",
                            "id": "ni_169148538818572",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_axi_1",
                            "id": "ni_169148538818573",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_axi_2",
                            "id": "ni_169148538818574",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [
                        {"name": "S_COUNT", "id": "169148538818556", "value": "1"},
                        {"name": "M_COUNT", "id": "169148538818557", "value": "3"},
                        {"name": "DATA_WIDTH", "id": "169148538818558", "value": "32"},
                        {"name": "ADDR_WIDTH", "id": "169148538818559", "value": "32"},
                        {"name": "ID_WIDTH", "id": "169148538818560", "value": "12"},
                        {
                            "name": "M_BASE_ADDR",
                            "id": "169148538818561",
                            "value": "118'h43c2000043c1000043c00000",
                        },
                        {
                            "name": "M_ADDR_WIDTH",
                            "id": "169148538818562",
                            "value": "96'h100000001000000010",
                        },
                        {"name": "AWUSER_WIDTH", "id": "169148538818563", "value": "1"},
                        {"name": "WUSER_WIDTH", "id": "169148538818564", "value": "1"},
                        {"name": "ARUSER_WIDTH", "id": "169148538818565", "value": "1"},
                        {"name": "BUSER_WIDTH", "id": "169148538818566", "value": "1"},
                        {"name": "RUSER_WIDTH", "id": "169148538818567", "value": "1"},
                        {"name": "STRB_WIDTH", "id": "169148538818568", "value": "DATA_WIDTH/8"},
                    ],
                    "name": "axi_interconnect0",
                },
                {
                    "type": "axi_axil_adapter",
                    "id": "node_169148538818586",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "clk",
                            "id": "ni_169148538818582",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "rst",
                            "id": "ni_169148538818583",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axi",
                            "id": "ni_169148538818584",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "m_axi",
                            "id": "ni_169148538818585",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [
                        {"name": "ADDR_WIDTH", "id": "169148538818576", "value": "32"},
                        {"name": "AXI_DATA_WIDTH", "id": "169148538818577", "value": "32"},
                        {"name": "AXI_ID_WIDTH", "id": "169148538818578", "value": "12"},
                        {
                            "name": "AXI_STRB_WIDTH",
                            "id": "169148538818579",
                            "value": "AXI_DATA_WIDTH/8",
                        },
                        {"name": "AXIL_DATA_WIDTH", "id": "169148538818580", "value": "32"},
                        {
                            "name": "AXIL_STRB_WIDTH",
                            "id": "169148538818581",
                            "value": "AXIL_DATA_WIDTH/8",
                        },
                    ],
                    "name": "axi_bridge_disp",
                },
                {
                    "type": "axi_axil_adapter",
                    "id": "node_169148538818597",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "clk",
                            "id": "ni_169148538818593",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "rst",
                            "id": "ni_169148538818594",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axi",
                            "id": "ni_169148538818595",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "m_axi",
                            "id": "ni_169148538818596",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [
                        {"name": "ADDR_WIDTH", "id": "169148538818587", "value": "32"},
                        {"name": "AXI_DATA_WIDTH", "id": "169148538818588", "value": "32"},
                        {"name": "AXI_ID_WIDTH", "id": "169148538818589", "value": "12"},
                        {
                            "name": "AXI_STRB_WIDTH",
                            "id": "169148538818590",
                            "value": "AXI_DATA_WIDTH/8",
                        },
                        {"name": "AXIL_DATA_WIDTH", "id": "169148538818591", "value": "32"},
                        {
                            "name": "AXIL_STRB_WIDTH",
                            "id": "169148538818592",
                            "value": "AXIL_DATA_WIDTH/8",
                        },
                    ],
                    "name": "axi_bridge_dma",
                },
                {
                    "type": "axi_axil_adapter",
                    "id": "node_1691485388185108",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "clk",
                            "id": "ni_1691485388185104",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "rst",
                            "id": "ni_1691485388185105",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axi",
                            "id": "ni_1691485388185106",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "m_axi",
                            "id": "ni_1691485388185107",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [
                        {"name": "ADDR_WIDTH", "id": "169148538818598", "value": "32"},
                        {"name": "AXI_DATA_WIDTH", "id": "169148538818599", "value": "32"},
                        {"name": "AXI_ID_WIDTH", "id": "1691485388185100", "value": "12"},
                        {
                            "name": "AXI_STRB_WIDTH",
                            "id": "1691485388185101",
                            "value": "AXI_DATA_WIDTH/8",
                        },
                        {"name": "AXIL_DATA_WIDTH", "id": "1691485388185102", "value": "32"},
                        {
                            "name": "AXIL_STRB_WIDTH",
                            "id": "1691485388185103",
                            "value": "AXIL_DATA_WIDTH/8",
                        },
                    ],
                    "name": "axi_bridge_mmcm",
                },
                {
                    "type": "axis_dwidth_converter",
                    "id": "node_1691485388185115",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "aclk",
                            "id": "ni_1691485388185111",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "aresetn",
                            "id": "ni_1691485388185112",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axis",
                            "id": "ni_1691485388185113",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "m_axis",
                            "id": "ni_1691485388185114",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [
                        {"name": "IN_DATA_WIDTH", "id": "1691485388185109", "value": "64"},
                        {"name": "OUT_DATA_WIDTH", "id": "1691485388185110", "value": "32"},
                    ],
                    "name": "axis_dwidth_converter",
                },
                {
                    "type": "clock_crossing",
                    "id": "node_1691485388185120",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "clkA",
                            "id": "ni_1691485388185116",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "A",
                            "id": "ni_1691485388185117",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "clkB",
                            "id": "ni_1691485388185118",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "B",
                            "id": "ni_1691485388185119",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "clock_crossing",
                },
                {
                    "type": "proc_sys_reset",
                    "id": "node_1691485388185131",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "slowest_sync_clk",
                            "id": "ni_1691485388185121",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "ext_reset_in",
                            "id": "ni_1691485388185122",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "aux_reset_in",
                            "id": "ni_1691485388185123",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "mb_debug_sys_rst",
                            "id": "ni_1691485388185124",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "dcm_locked",
                            "id": "ni_1691485388185125",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "mb_reset",
                            "id": "ni_1691485388185126",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "bus_struct_reset",
                            "id": "ni_1691485388185127",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "peripheral_reset",
                            "id": "ni_1691485388185128",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "interconnect_aresetn",
                            "id": "ni_1691485388185129",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "peripheral_aresetn",
                            "id": "ni_1691485388185130",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "reset0",
                },
                {
                    "type": "proc_sys_reset",
                    "id": "node_1691485388185142",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "slowest_sync_clk",
                            "id": "ni_1691485388185132",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "ext_reset_in",
                            "id": "ni_1691485388185133",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "aux_reset_in",
                            "id": "ni_1691485388185134",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "mb_debug_sys_rst",
                            "id": "ni_1691485388185135",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "dcm_locked",
                            "id": "ni_1691485388185136",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "mb_reset",
                            "id": "ni_1691485388185137",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "bus_struct_reset",
                            "id": "ni_1691485388185138",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "peripheral_reset",
                            "id": "ni_1691485388185139",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "interconnect_aresetn",
                            "id": "ni_1691485388185140",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "peripheral_aresetn",
                            "id": "ni_1691485388185141",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "reset1",
                },
                {
                    "type": "axis_async_fifo",
                    "id": "node_1691485388185161",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "async_rst",
                            "id": "ni_1691485388185150",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_clk",
                            "id": "ni_1691485388185151",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "m_clk",
                            "id": "ni_1691485388185152",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_axis",
                            "id": "ni_1691485388185159",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "s_status_overflow",
                            "id": "ni_1691485388185153",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "s_status_bad_frame",
                            "id": "ni_1691485388185154",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "s_status_good_frame",
                            "id": "ni_1691485388185155",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_status_overflow",
                            "id": "ni_1691485388185156",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_status_bad_frame",
                            "id": "ni_1691485388185157",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_status_good_frame",
                            "id": "ni_1691485388185158",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "m_axis",
                            "id": "ni_1691485388185160",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [
                        {"name": "DATA_WIDTH", "id": "1691485388185143", "value": "64"},
                        {
                            "name": "KEEP_WIDTH",
                            "id": "1691485388185144",
                            "value": "(DATA_WIDTH+7)/8",
                        },
                        {"name": "ID_WIDTH", "id": "1691485388185145", "value": "8"},
                        {"name": "DEST_WIDTH", "id": "1691485388185146", "value": "8"},
                        {"name": "USER_WIDTH", "id": "1691485388185147", "value": "1"},
                        {"name": "ID_ENABLE", "id": "1691485388185148", "value": "0"},
                        {"name": "USER_ENABLE", "id": "1691485388185149", "value": "0"},
                    ],
                    "name": "axis_clock_converter",
                },
                {
                    "type": "ps7",
                    "id": "node_1691485388185198",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "MAXIGP0ACLK",
                            "id": "ni_1691485388185162",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "SAXIHP0ACLK",
                            "id": "ni_1691485388185163",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "IRQ_F2P_0",
                            "id": "ni_1691485388185164",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "IRQ_F2P_1",
                            "id": "ni_1691485388185165",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "ddr_addr",
                            "id": "ni_1691485388185175",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_bankaddr",
                            "id": "ni_1691485388185176",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_cas_n",
                            "id": "ni_1691485388185177",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_cke",
                            "id": "ni_1691485388185178",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_clk",
                            "id": "ni_1691485388185179",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_clk_n",
                            "id": "ni_1691485388185180",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_cs_n",
                            "id": "ni_1691485388185181",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_dm",
                            "id": "ni_1691485388185182",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_dq",
                            "id": "ni_1691485388185183",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_dqs",
                            "id": "ni_1691485388185184",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_dqs_n",
                            "id": "ni_1691485388185185",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_drstb",
                            "id": "ni_1691485388185186",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_odt",
                            "id": "ni_1691485388185187",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_ras_n",
                            "id": "ni_1691485388185188",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_vr_n",
                            "id": "ni_1691485388185189",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_vr",
                            "id": "ni_1691485388185190",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ddr_web",
                            "id": "ni_1691485388185191",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ps_mio",
                            "id": "ni_1691485388185192",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ps_clk",
                            "id": "ni_1691485388185193",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ps_porb",
                            "id": "ni_1691485388185194",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "ps_srstb",
                            "id": "ni_1691485388185195",
                            "direction": "inout",
                            "side": "right",
                        },
                        {
                            "name": "S_AXI_HP0",
                            "id": "ni_1691485388185196",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "FCLK0",
                            "id": "ni_1691485388185166",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "FCLK1",
                            "id": "ni_1691485388185167",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "MAXIGP0ARESETN",
                            "id": "ni_1691485388185168",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "SAXIHP0ARESETN",
                            "id": "ni_1691485388185169",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "FCLK_RESET0_N",
                            "id": "ni_1691485388185170",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "SAXIHP0RACOUNT",
                            "id": "ni_1691485388185171",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "SAXIHP0RCOUNT",
                            "id": "ni_1691485388185172",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "SAXIHP0WACOUNT",
                            "id": "ni_1691485388185173",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "SAXIHP0WCOUNT",
                            "id": "ni_1691485388185174",
                            "direction": "output",
                            "side": "right",
                        },
                        {
                            "name": "M_AXI_GP0",
                            "id": "ni_1691485388185197",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "ps7",
                },
                {
                    "type": "axi_protocol_converter",
                    "id": "node_1691485388185203",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "aclk",
                            "id": "ni_1691485388185199",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "aresetn",
                            "id": "ni_1691485388185200",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "S_AXI",
                            "id": "ni_1691485388185201",
                            "direction": "input",
                            "side": "left",
                        },
                        {
                            "name": "M_AXI",
                            "id": "ni_1691485388185202",
                            "direction": "output",
                            "side": "right",
                        },
                    ],
                    "properties": [],
                    "name": "axi_protocol_converter0",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185206",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185205",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185204", "value": "HDMI_CLK_P"}
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185209",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185208",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185207", "value": "HDMI_CLK_N"}
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185212",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185211",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185210", "value": "HDMI_D0_P"}
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185215",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185214",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185213", "value": "HDMI_D0_N"}
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185218",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185217",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185216", "value": "HDMI_D1_P"}
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185221",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185220",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185219", "value": "HDMI_D1_N"}
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185224",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185223",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185222", "value": "HDMI_D2_P"}
                    ],
                    "name": "External Output",
                },
                {
                    "type": "External Output",
                    "id": "node_1691485388185227",
                    "position": {"x": 0, "y": 0},
                    "width": 200,
                    "twoColumn": False,
                    "interfaces": [
                        {
                            "name": "external",
                            "id": "ni_1691485388185226",
                            "direction": "input",
                            "side": "left",
                        }
                    ],
                    "properties": [
                        {"name": "External Name", "id": "1691485388185225", "value": "HDMI_D2_N"}
                    ],
                    "name": "External Output",
                },
            ],
            "connections": [
                {
                    "id": "1691485388185228",
                    "from": "ni_1691485388185202",
                    "to": "ni_1691485388185196",
                },
                {
                    "id": "1691485388185229",
                    "from": "ni_16914853881858",
                    "to": "ni_1691485388185201",
                },
                {
                    "id": "1691485388185230",
                    "from": "ni_1691485388185197",
                    "to": "ni_169148538818571",
                },
                {
                    "id": "1691485388185231",
                    "from": "ni_169148538818574",
                    "to": "ni_169148538818584",
                },
                {
                    "id": "1691485388185232",
                    "from": "ni_169148538818573",
                    "to": "ni_169148538818595",
                },
                {
                    "id": "1691485388185233",
                    "from": "ni_169148538818572",
                    "to": "ni_1691485388185106",
                },
                {
                    "id": "1691485388185234",
                    "from": "ni_1691485388185107",
                    "to": "ni_169148538818554",
                },
                {"id": "1691485388185235", "from": "ni_169148538818596", "to": "ni_16914853881856"},
                {
                    "id": "1691485388185236",
                    "from": "ni_1691485388185160",
                    "to": "ni_1691485388185113",
                },
                {
                    "id": "1691485388185237",
                    "from": "ni_16914853881857",
                    "to": "ni_1691485388185159",
                },
                {
                    "id": "1691485388185238",
                    "from": "ni_1691485388185114",
                    "to": "ni_169148538818525",
                },
                {
                    "id": "1691485388185239",
                    "from": "ni_169148538818585",
                    "to": "ni_169148538818524",
                },
                {
                    "id": "1691485388185240",
                    "from": "ni_1691485388185166",
                    "to": "ni_1691485388185162",
                },
                {
                    "id": "1691485388185241",
                    "from": "ni_1691485388185166",
                    "to": "ni_1691485388185163",
                },
                {
                    "id": "1691485388185242",
                    "from": "ni_16914853881854",
                    "to": "ni_1691485388185164",
                },
                {
                    "id": "1691485388185243",
                    "from": "ni_16914853881855",
                    "to": "ni_1691485388185165",
                },
                {
                    "id": "1691485388185244",
                    "from": "ni_1691485388185166",
                    "to": "ni_1691485388185199",
                },
                {
                    "id": "1691485388185245",
                    "from": "ni_1691485388185129",
                    "to": "ni_1691485388185200",
                },
                {
                    "id": "1691485388185246",
                    "from": "ni_1691485388185166",
                    "to": "ni_1691485388185121",
                },
                {
                    "id": "1691485388185247",
                    "from": "ni_169148538818551",
                    "to": "ni_1691485388185132",
                },
                {
                    "id": "1691485388185248",
                    "from": "ni_1691485388185166",
                    "to": "ni_169148538818569",
                },
                {
                    "id": "1691485388185249",
                    "from": "ni_1691485388185127",
                    "to": "ni_169148538818570",
                },
                {
                    "id": "1691485388185250",
                    "from": "ni_1691485388185166",
                    "to": "ni_169148538818582",
                },
                {
                    "id": "1691485388185251",
                    "from": "ni_1691485388185127",
                    "to": "ni_169148538818583",
                },
                {
                    "id": "1691485388185252",
                    "from": "ni_1691485388185166",
                    "to": "ni_1691485388185104",
                },
                {
                    "id": "1691485388185253",
                    "from": "ni_1691485388185127",
                    "to": "ni_1691485388185105",
                },
                {
                    "id": "1691485388185254",
                    "from": "ni_1691485388185166",
                    "to": "ni_169148538818593",
                },
                {
                    "id": "1691485388185255",
                    "from": "ni_1691485388185127",
                    "to": "ni_169148538818594",
                },
                {
                    "id": "1691485388185256",
                    "from": "ni_1691485388185166",
                    "to": "ni_169148538818548",
                },
                {
                    "id": "1691485388185257",
                    "from": "ni_1691485388185128",
                    "to": "ni_169148538818549",
                },
                {
                    "id": "1691485388185258",
                    "from": "ni_1691485388185167",
                    "to": "ni_169148538818550",
                },
                {
                    "id": "1691485388185259",
                    "from": "ni_1691485388185166",
                    "to": "ni_16914853881850",
                },
                {
                    "id": "1691485388185260",
                    "from": "ni_1691485388185128",
                    "to": "ni_16914853881851",
                },
                {
                    "id": "1691485388185261",
                    "from": "ni_1691485388185119",
                    "to": "ni_16914853881852",
                },
                {
                    "id": "1691485388185262",
                    "from": "ni_1691485388185119",
                    "to": "ni_16914853881853",
                },
                {
                    "id": "1691485388185263",
                    "from": "ni_169148538818551",
                    "to": "ni_1691485388185116",
                },
                {
                    "id": "1691485388185264",
                    "from": "ni_169148538818514",
                    "to": "ni_1691485388185117",
                },
                {
                    "id": "1691485388185265",
                    "from": "ni_1691485388185166",
                    "to": "ni_1691485388185118",
                },
                {
                    "id": "1691485388185266",
                    "from": "ni_169148538818551",
                    "to": "ni_1691485388185111",
                },
                {
                    "id": "1691485388185267",
                    "from": "ni_1691485388185140",
                    "to": "ni_1691485388185112",
                },
                {
                    "id": "1691485388185268",
                    "from": "ni_1691485388185127",
                    "to": "ni_1691485388185150",
                },
                {
                    "id": "1691485388185269",
                    "from": "ni_1691485388185166",
                    "to": "ni_1691485388185151",
                },
                {
                    "id": "1691485388185270",
                    "from": "ni_169148538818551",
                    "to": "ni_1691485388185152",
                },
                {
                    "id": "1691485388185271",
                    "from": "ni_169148538818551",
                    "to": "ni_169148538818510",
                },
                {
                    "id": "1691485388185272",
                    "from": "ni_169148538818553",
                    "to": "ni_169148538818511",
                },
                {
                    "id": "1691485388185273",
                    "from": "ni_1691485388185166",
                    "to": "ni_169148538818512",
                },
                {
                    "id": "1691485388185274",
                    "from": "ni_1691485388185130",
                    "to": "ni_169148538818513",
                },
                {
                    "id": "1691485388185275",
                    "from": "ni_169148538818551",
                    "to": "ni_169148538818527",
                },
                {
                    "id": "1691485388185276",
                    "from": "ni_169148538818552",
                    "to": "ni_169148538818528",
                },
                {
                    "id": "1691485388185277",
                    "from": "ni_169148538818553",
                    "to": "ni_169148538818529",
                },
                {
                    "id": "1691485388185278",
                    "from": "ni_169148538818515",
                    "to": "ni_169148538818530",
                },
                {
                    "id": "1691485388185279",
                    "from": "ni_169148538818516",
                    "to": "ni_169148538818531",
                },
                {
                    "id": "1691485388185280",
                    "from": "ni_169148538818517",
                    "to": "ni_169148538818532",
                },
                {
                    "id": "1691485388185281",
                    "from": "ni_169148538818518",
                    "to": "ni_169148538818533",
                },
                {
                    "id": "1691485388185282",
                    "from": "ni_169148538818519",
                    "to": "ni_169148538818534",
                },
                {
                    "id": "1691485388185283",
                    "from": "ni_169148538818520",
                    "to": "ni_169148538818535",
                },
                {
                    "id": "1691485388185284",
                    "from": "ni_169148538818521",
                    "to": "ni_169148538818536",
                },
                {
                    "id": "1691485388185285",
                    "from": "ni_169148538818522",
                    "to": "ni_169148538818537",
                },
                {
                    "id": "1691485388185286",
                    "from": "ni_169148538818523",
                    "to": "ni_169148538818538",
                },
                {
                    "id": "1691485388185287",
                    "from": "ni_169148538818539",
                    "to": "ni_1691485388185205",
                },
                {
                    "id": "1691485388185288",
                    "from": "ni_169148538818540",
                    "to": "ni_1691485388185208",
                },
                {
                    "id": "1691485388185289",
                    "from": "ni_169148538818545",
                    "to": "ni_1691485388185211",
                },
                {
                    "id": "1691485388185290",
                    "from": "ni_169148538818546",
                    "to": "ni_1691485388185214",
                },
                {
                    "id": "1691485388185291",
                    "from": "ni_169148538818543",
                    "to": "ni_1691485388185217",
                },
                {
                    "id": "1691485388185292",
                    "from": "ni_169148538818544",
                    "to": "ni_1691485388185220",
                },
                {
                    "id": "1691485388185293",
                    "from": "ni_169148538818541",
                    "to": "ni_1691485388185223",
                },
                {
                    "id": "1691485388185294",
                    "from": "ni_169148538818542",
                    "to": "ni_1691485388185226",
                },
            ],
            "panning": {"x": 1451.9736283063444, "y": -28.825912977567043},
            "scaling": 0.6250056657338314,
        },
        "graphTemplateInstances": [],
        "version": "20230619.3",
    }
