# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0


class TestDesign:
    def test_design(self):
        from fpga_topwrap.design import build_design

        build_design('tests/data/design.yaml')
