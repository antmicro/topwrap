# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path


class TestDesign:
    def test_design(self):
        from topwrap.design import build_design_from_yaml

        build_design_from_yaml(Path("tests/data/data_build/design.yaml"), Path("build"))
