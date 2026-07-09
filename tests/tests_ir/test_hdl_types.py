# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from topwrap.model.hdl_types import Bits, Dimensions
from topwrap.model.misc import ElaboratableValue


class TestLogicArraySize:
    def test_single_dimension_matches_the_per_dimension_formula(self):
        # size == item_size * (upper - lower + 1); logic[7:0] is 8 bits.
        b = Bits(dimensions=[Dimensions(upper=ElaboratableValue(7), lower=ElaboratableValue(0))])
        assert b.size.elaborate() == 8

    def test_multi_dimension_multiplies_all_dimensions(self):
        b = Bits(
            dimensions=[
                Dimensions(upper=ElaboratableValue(7), lower=ElaboratableValue(0)),
                Dimensions(upper=ElaboratableValue(3), lower=ElaboratableValue(0)),
            ]
        )
        assert b.size.elaborate() == 32

    def test_empty_dimensions_defaults_to_item_size(self):
        # Product over zero dimensions is the identity (1), so size == item size.
        b = Bits(dimensions=[])
        assert b.size.elaborate() == 1

    def test_symbolic_dimension_stays_symbolic(self):
        # Unresolved dims should elaborate() to None, not raise.
        b = Bits(
            dimensions=[Dimensions(upper=ElaboratableValue("WIDTH-1"), lower=ElaboratableValue(0))]
        )
        assert b.size.elaborate() is None
