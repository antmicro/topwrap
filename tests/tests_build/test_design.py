# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


class TestDesign:
    def test_design(self):
        from fpga_topwrap.design import build_design_from_yaml

        build_design_from_yaml("tests/data/data_build/design.yaml", "build")
