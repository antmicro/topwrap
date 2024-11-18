# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from topwrap.design import DesignDescription


class TestDesign:
    def test_design(self):
        path = Path("tests/data/data_build/design.yaml")
        design = DesignDescription.load(path)
        ipc = design.to_ip_connect(path.parent)

        ipc.generate_top("top")
        ipc.generate_fuse_core()

    def test_clog2_build(self):
        results = []

        for path in Path().glob("tests/data/data_build/clog2/clog2_design*.yaml"):
            design = DesignDescription.load(path)
            ipc = design.to_ip_connect(path.parent)

            ipc.generate_top("top")
            ipc.generate_fuse_core(sources_dir=[Path("tests/data/data_build/clog2/")])

            with open("build/top.v") as out:
                results.append(out.read())

        assert len(results) == 2
        assert results[0] == results[1]
