# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path


class TestDesign:
    def test_design(self):
        from topwrap.design import build_design_from_yaml

        build_design_from_yaml(Path("tests/data/data_build/design.yaml"), Path("build"))

    def test_clog2_build(self):
        from topwrap.design import build_design_from_yaml

        build_design_from_yaml(
            Path("tests/data/data_build/clog2/clog2_design.yaml"),
            Path("build"),
            [Path("tests/data/data_build/clog2/")],
        )

        with open("build/top.v") as e:
            result1 = e.read()

        build_design_from_yaml(
            Path("tests/data/data_build/clog2/clog2_design2.yaml"),
            Path("build"),
            [Path("tests/data/data_build/clog2/")],
        )

        with open("build/top.v") as e:
            result2 = e.read()

        assert result1 == result2
