# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import json


def read_json_file(json_file_path: str) -> str:
    with open(json_file_path, "r") as json_file:
        json_contents = json.load(json_file)
    return json_contents
