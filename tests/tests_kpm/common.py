# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json

AXI_NAME = "axi_bridge"
PS7_NAME = "ps7"
PWM_NAME = "litex_pwm_top"


def read_json_file(json_file_path: str) -> str:
    with open(json_file_path, "r") as json_file:
        json_contents = json.load(json_file)
    return json_contents
