# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re

from topwrap.model.connections import PortDirection
from topwrap.model.hdl_types import Bits, Dimensions, ElabvalueEvaluator, LogicArray
from topwrap.model.interface import (
    Interface,
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module


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


class TestElabvalueEvaluator:
    def test_unbased_zero(self):
        assert ElabvalueEvaluator._sanitize("'0") == "0"

    def test_intf_params_resolving(self):
        intf = InterfaceDefinition(
            id=Identifier("nasty_interface"),
            parameters=[
                Parameter(name="indep_1", default_value=ElaboratableValue("'d32")),
                Parameter(name="clog2", default_value=ElaboratableValue("$clog2(indep_1)")),
                Parameter(name="COLLISION", default_value=ElaboratableValue("1337")),
                Parameter(name="COLLISION_CHECKER", default_value=ElaboratableValue("COLLISION/2")),
                Parameter(name="COLLISION_TAKER_AUX", default_value=ElaboratableValue("8'd16")),
            ],
            signals=[
                InterfaceSignal(
                    name="indep",
                    regexp=re.compile("indep"),
                    type=Bits(
                        dimensions=[
                            Dimensions(
                                upper=ElaboratableValue("indep_1 + 32 * 2"),
                                lower=ElaboratableValue("0"),
                            )
                        ]
                    ),
                    modes={
                        InterfaceMode.MANAGER: InterfaceSignalConfiguration(PortDirection.IN, True),
                        InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                            PortDirection.OUT, True
                        ),
                    },
                ),
                InterfaceSignal(
                    name="clog",
                    regexp=re.compile("clog"),
                    type=Bits(
                        dimensions=[
                            Dimensions(
                                upper=ElaboratableValue("clog2-1"), lower=ElaboratableValue("0")
                            )
                        ]
                    ),
                    modes={
                        InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                            PortDirection.OUT, True
                        ),
                        InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                            PortDirection.IN, True
                        ),
                    },
                ),
                InterfaceSignal(
                    name="col_ins",
                    regexp=re.compile("col_ins"),
                    type=Bits(
                        dimensions=[
                            Dimensions(
                                upper=ElaboratableValue("COLLISION_CHECKER-1"),
                                lower=ElaboratableValue("0"),
                            )
                        ]
                    ),
                    modes={
                        InterfaceMode.MANAGER: InterfaceSignalConfiguration(PortDirection.IN, True),
                        InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                            PortDirection.OUT, True
                        ),
                    },
                ),
                InterfaceSignal(
                    name="col_aux",
                    regexp=re.compile("col_aux"),
                    type=Bits(
                        dimensions=[
                            Dimensions(
                                upper=ElaboratableValue("COLLISION_TAKER_AUX-1"),
                                lower=ElaboratableValue("0"),
                            )
                        ]
                    ),
                    modes={
                        InterfaceMode.MANAGER: InterfaceSignalConfiguration(
                            PortDirection.OUT, True
                        ),
                        InterfaceMode.SUBORDINATE: InterfaceSignalConfiguration(
                            PortDirection.IN, True
                        ),
                    },
                ),
            ],
        )

        mod = Module(
            id=Identifier("test_module"),
            parameters=[Parameter(name="COLLISION", default_value=ElaboratableValue(10))],
            interfaces=[
                Interface(
                    "try_me",
                    mode=InterfaceMode.MANAGER,
                    definition=intf,
                    signals={
                        intf.signals.find_by_name_or_error("indep")._id: None,
                        intf.signals.find_by_name_or_error("clog")._id: None,
                        intf.signals.find_by_name_or_error("col_ins")._id: None,
                        intf.signals.find_by_name_or_error("col_aux")._id: None,
                    },
                    parameters={
                        intf.parameters.find_by_name_or_error(
                            "COLLISION_TAKER_AUX"
                        )._id: ElaboratableValue("COLLISION")
                    },
                )
            ],
        )

        params, sigs = ElabvalueEvaluator.resolve_intf_values(
            mod.interfaces[0], {mod.parameters[0]._id: ElaboratableValue(10)}
        )
        assert params[
            intf.parameters.find_by_name_or_error("COLLISION_TAKER_AUX")._id
        ] == ElaboratableValue(10)

        sig = sigs[intf.signals.find_by_name_or_error("indep")._id]
        assert isinstance(sig, LogicArray)
        assert sig.dimensions[0] == Dimensions(
            upper=ElaboratableValue(96), lower=ElaboratableValue(0)
        )

        sig = sigs[intf.signals.find_by_name_or_error("clog")._id]
        assert isinstance(sig, LogicArray)
        assert sig.dimensions[0] == Dimensions(
            upper=ElaboratableValue(4), lower=ElaboratableValue(0)
        )

        sig = sigs[intf.signals.find_by_name_or_error("col_ins")._id]
        assert isinstance(sig, LogicArray)
        assert sig.dimensions[0] == Dimensions(
            upper=ElaboratableValue(667), lower=ElaboratableValue(0)
        )

        sig = sigs[intf.signals.find_by_name_or_error("col_aux")._id]
        assert isinstance(sig, LogicArray)
        assert sig.dimensions[0] == Dimensions(
            upper=ElaboratableValue(9), lower=ElaboratableValue(0)
        )
