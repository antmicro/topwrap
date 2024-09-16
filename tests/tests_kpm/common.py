# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from topwrap.util import JsonType

AXI_NAME = "axi_bridge"
PS7_NAME = "ps7"
PWM_NAME = "litex_pwm_top"
TEST_DATA_PATH = "tests/data/data_kpm/"


def read_json_file(json_file_path: Path) -> JsonType:
    with open(json_file_path, "r") as json_file:
        json_contents = json.load(json_file)
    return json_contents


def save_file_to_json(file_path: Path, file_name: str, file_content: JsonType):
    with open(Path(file_path / file_name), "w") as json_file:
        json.dump(file_content, json_file)
