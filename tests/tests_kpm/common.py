# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json

SPEC_METANODES = 4  # Unique metanodes: Input, Output, Inout, Constant

# PWM
PWM_IPCORE_NODES = 3  # All IP Cores from examples/pwm/project.yml

PWM_UNIQUE_IPCORE_NODES = 3  # Unique IP Cores from examples/pwm/project.yml
PWM_ALL_UNIQUE_NODES = PWM_UNIQUE_IPCORE_NODES + SPEC_METANODES

PWM_EXTERNAL_METANODES = 1  # Unique external metanodes
PWM_CONSTANT_METANODES = 0  # Unique constant metanodes
PWM_METANODES = PWM_EXTERNAL_METANODES + PWM_CONSTANT_METANODES

PWM_CORE_AXI_CONNECTIONS = 4  # Connections to AXI bridge
PWM_CORE_PS7_CONNECTIONS = 7  # Connections to PS7 module
PWM_CORE_PWM_CONNECTIONS = 3  # Connections to PWM module

# HDMI
HDMI_IPCORE_NODES = 15  # All IP Cores from examples/hdmi/project.yml

HDMI_UNIQUE_IPCORE_NODES = 12  # Unique IP Cores from examples/hdmi/project.yml
HDMI_ALL_UNIQUE_NODES = HDMI_UNIQUE_IPCORE_NODES + SPEC_METANODES

HDMI_EXTERNAL_METANODES = 29  # Unique external metanodes
HDMI_CONSTANT_METANODES = 2  # Unique constant metanodes
HDMI_METANODES = HDMI_EXTERNAL_METANODES + HDMI_CONSTANT_METANODES

HDMI_IPCORES_CONNECTIONS = 59  # Connections between IP Cores
HDMI_EXTERNAL_CONNECTIONS = 29  # Connections to external metanodes
HDMI_CONSTANT_CONNECTIONS = 8  # Connections to constant metanodes
HDMI_CONNECTIONS = HDMI_IPCORES_CONNECTIONS + HDMI_EXTERNAL_CONNECTIONS + HDMI_CONSTANT_CONNECTIONS


def read_json_file(json_file_path: str) -> str:
    with open(json_file_path, "r") as json_file:
        json_contents = json.load(json_file)
    return json_contents
