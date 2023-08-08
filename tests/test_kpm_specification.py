# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0

import jsonschema


def test_pwm_specification_generation(specification_schema, pwm_ipcores_yamls):
    from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

    pwm_specification = ipcore_yamls_to_kpm_spec(pwm_ipcores_yamls)
    assert len(pwm_specification["nodes"]) == 6  # 3 IP cores + 3 External metanodes
    jsonschema.validate(pwm_specification, specification_schema)


def test_hdmi_specification_generation(specification_schema, hdmi_ipcores_yamls):
    from fpga_topwrap.yamls_to_kpm_spec_parser import ipcore_yamls_to_kpm_spec

    hdmi_specification = ipcore_yamls_to_kpm_spec(hdmi_ipcores_yamls)
    assert len(hdmi_specification["nodes"]) == 15  # 12 IP cores + 3 External metanodes
    jsonschema.validate(hdmi_specification, specification_schema)
