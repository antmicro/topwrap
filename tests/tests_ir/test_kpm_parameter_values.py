# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import pytest

from topwrap.backend.kpm.common import elab_val_to_kpm_val
from topwrap.backend.yaml.common.types import ComplexParameter
from topwrap.frontend.kpm.common import kpm_val_to_elab_val
from topwrap.model.misc import ElaboratableValue


@pytest.mark.parametrize("value", [233, "WIDTH+1"])
def test_complex_parameter_kpm_round_trip(value):
    parameter = ComplexParameter(width=32, value=value)
    original = ElaboratableValue(parameter)
    serialized = elab_val_to_kpm_val(original)
    assert serialized == original.value
    assert kpm_val_to_elab_val(serialized).raw == parameter


def test_legacy_complex_parameter_kpm_value():
    value = kpm_val_to_elab_val("{'value': 'WIDTH+1', 'width': 32}")
    assert value.raw == ComplexParameter(width=32, value="WIDTH+1")
