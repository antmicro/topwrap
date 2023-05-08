# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

class TestKPMSpec:
    def test_ipcore_to_kpm(self):
        from fpga_topwrap.yamls_to_kpm_spec_parser import _ipcore_to_kpm
        yamlfiles = [
            'tests/data/axi_dispctrl_v1_0.yaml',
            'tests/data/DMATop.yaml'
        ]
        for yamlfile in yamlfiles:
            _ipcore_to_kpm(yamlfile)
