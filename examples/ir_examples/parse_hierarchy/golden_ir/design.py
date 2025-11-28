# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

# Golden IR file
# Describes the following hierarchy:
# A
# |-> B
# |-> C
#     |-> D

from topwrap.model.connections import (
    ConstantConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.misc import ElaboratableValue, Identifier, Parameter
from topwrap.model.module import Module

_concat_modules: dict[int, Module] = {}


def make_concat_mod(n: int) -> Module:
    if n in _concat_modules:
        return _concat_modules[n]

    ports = [Port(name=f"in{i}", direction=PortDirection.IN) for i in range(n)]
    ports.append(Port(name="out", direction=PortDirection.OUT))

    mod = Module(
        id=Identifier(name=f"concat_{n}"),
        ports=ports,
    )
    _concat_modules[n] = mod
    return mod


_select_modules: dict[str, Module] = {}


def make_select_mod(select_name: str) -> Module:
    if select_name in _select_modules:
        return _select_modules[select_name]

    var_name = select_name.split("[")[0]
    ports = [
        Port(name=var_name, direction=PortDirection.IN),
        Port(name=select_name, direction=PortDirection.OUT),
    ]

    mod = Module(
        id=Identifier(name=select_name),
        ports=ports,
    )
    _select_modules[select_name] = mod
    return mod


TOPWRAP_CONTROL = Module(
    id=Identifier(name="A.(control)", vendor="topwrap", library="internal"),
    ports=[
        Port(name="top.clk", direction=PortDirection.IN),
        Port(name="top.a_b_in", direction=PortDirection.IN),
        Port(name="binst.b_in", direction=PortDirection.OUT),
        Port(name="top.clocked_out", direction=PortDirection.OUT),
        Port(name="top.logicdriver", direction=PortDirection.IN),
    ],
)


B_ports = [
    Port(name="b_in", direction=PortDirection.IN),
    Port(name="b_out", direction=PortDirection.OUT),
]

B_param = Parameter(name="Bparam", default_value=ElaboratableValue("1'b0"))

B = Module(
    id=Identifier(name="B"),
    ports=B_ports,
    parameters=[B_param],
    design=Design(
        connections=[
            PortConnection(
                source=ReferencedPort.external(B_ports[0]),
                target=ReferencedPort.external(B_ports[1]),
            )
        ]
    ),
)

# Single-bit passthrough module
D_ports = [
    Port(name="d_in", direction=PortDirection.IN),
    Port(name="d_out", direction=PortDirection.OUT),
]

D = Module(
    id=Identifier(name="D"),
    ports=D_ports,
    design=Design(
        connections=[
            PortConnection(
                source=ReferencedPort.external(D_ports[0]),
                target=ReferencedPort.external(D_ports[1]),
            )
        ]
    ),
)

C_ports = [
    Port(name="c_in", direction=PortDirection.IN),
    Port(name="c_out", direction=PortDirection.OUT),
]

C_param_bit = Parameter(name="Cparam_bit", default_value=ElaboratableValue("1'b0"))
C_param_str = Parameter(name="Cparam_str", default_value=ElaboratableValue('""'))

inst_D = ModuleInstance(name="dinst", module=D)
C = Module(
    id=Identifier(name="C"),
    ports=C_ports,
    parameters=[C_param_bit, C_param_str],
    design=Design(
        components=[inst_D],
        connections=[
            PortConnection(
                source=ReferencedPort.external(C_ports[0]),
                target=ReferencedPort(instance=inst_D, io=D.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort.external(C_ports[1]),
                target=ReferencedPort(instance=inst_D, io=D.ports[1]),
            ),
        ],
    ),
)

A_ports = [
    Port(name="clk", direction=PortDirection.IN),
    Port(name="a_b_in", direction=PortDirection.IN),
    Port(name="a_c_in", direction=PortDirection.IN),
    Port(name="a_data_in", direction=PortDirection.IN),
    Port(name="logicdriver", direction=PortDirection.IN),
    Port(name="a_out", direction=PortDirection.OUT),
    Port(name="a_b_out", direction=PortDirection.OUT),
    Port(name="a_b_ext_out", direction=PortDirection.OUT),
    Port(name="a_b_ext_bitsel_out", direction=PortDirection.OUT),
    Port(name="a_bit_sel_out", direction=PortDirection.OUT),
    Port(name="a_range_sel_out", direction=PortDirection.OUT),
    Port(name="selfdriven_out", direction=PortDirection.OUT),
    Port(name="fordriven_out", direction=PortDirection.OUT),
    Port(name="clocked_out", direction=PortDirection.OUT),
]

A_param_consts = Parameter(name="CONSTS", default_value=ElaboratableValue("{1'b0, 1'b1}"))

inst_B = ModuleInstance(
    name="binst",
    module=B,
    parameters={B_param._id: ElaboratableValue("1'b1")},
)
inst_C = ModuleInstance(name="cinst", module=C)
inst_C2 = ModuleInstance(name="cinst2", module=C)
inst_genfor_C0 = ModuleInstance(
    name="genfor_cinst#0",
    module=C,
    parameters={
        C_param_bit._id: ElaboratableValue("CONSTS[0]"),
        C_param_str._id: ElaboratableValue('"tab[i]"'),
    },
)
inst_genfor_C1 = ModuleInstance(
    name="genfor_cinst#1",
    module=C,
    parameters={
        C_param_bit._id: ElaboratableValue("CONSTS[1]"),
        C_param_str._id: ElaboratableValue('"tab[i]"'),
    },
)
inst_logic = ModuleInstance(name="(control)", module=TOPWRAP_CONTROL)
inst_concat0 = ModuleInstance(name="concat_0", module=make_concat_mod(2))
inst_concat1 = ModuleInstance(name="concat_1", module=make_concat_mod(3))
inst_concat2 = ModuleInstance(name="concat_2", module=make_concat_mod(2))
inst_concat3 = ModuleInstance(name="concat_3", module=make_concat_mod(2))
inst_concat4 = ModuleInstance(name="concat_4", module=make_concat_mod(2))
inst_bitsel = ModuleInstance(name="a_data_in[3]", module=make_select_mod("a_data_in[3]"))
inst_rangesel = ModuleInstance(name="a_data_in[5:3]", module=make_select_mod("a_data_in[5:3]"))
inst_bitsel_data0 = ModuleInstance(name="a_data_in[0]", module=make_select_mod("a_data_in[0]"))

A = Module(
    id=Identifier(name="A"),
    ports=A_ports,
    parameters=[
        Parameter(name="PARAM1", default_value=ElaboratableValue(1)),
        A_param_consts,
    ],
    design=Design(
        components=[
            inst_B,
            inst_C,
            inst_C2,
            inst_genfor_C0,
            inst_genfor_C1,
            inst_logic,
            inst_concat0,
            inst_concat1,
            inst_concat2,
            inst_concat3,
            inst_concat4,
            inst_bitsel,
            inst_rangesel,
            inst_bitsel_data0,
        ],
        connections=[
            PortConnection(
                source=ReferencedPort.external(A_ports[0]),
                target=ReferencedPort(instance=inst_logic, io=TOPWRAP_CONTROL.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort.external(A_ports[1]),
                target=ReferencedPort(instance=inst_logic, io=TOPWRAP_CONTROL.ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_logic, io=TOPWRAP_CONTROL.ports[2]),
                target=ReferencedPort(instance=inst_B, io=B.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_logic, io=TOPWRAP_CONTROL.ports[3]),
                target=ReferencedPort.external(A_ports[13]),
            ),
            PortConnection(
                source=ReferencedPort.external(A_ports[4]),
                target=ReferencedPort(instance=inst_logic, io=TOPWRAP_CONTROL.ports[4]),
            ),
            PortConnection(
                source=ReferencedPort.external(A_ports[2]),
                target=ReferencedPort(instance=inst_C, io=C.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort.external(A_ports[2]),
                target=ReferencedPort(instance=inst_genfor_C0, io=C.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort.external(A_ports[2]),
                target=ReferencedPort(instance=inst_genfor_C1, io=C.ports[0]),
            ),
            # a_out = {b_out, c_out}
            PortConnection(
                source=ReferencedPort(instance=inst_B, io=B.ports[1]),
                target=ReferencedPort(instance=inst_concat0, io=inst_concat0.module.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_C, io=C.ports[1]),
                target=ReferencedPort(instance=inst_concat0, io=inst_concat0.module.ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_concat0, io=inst_concat0.module.ports[2]),
                target=ReferencedPort.external(A_ports[5]),
            ),
            # a_b_out = b_out
            PortConnection(
                source=ReferencedPort(instance=inst_B, io=B.ports[1]),
                target=ReferencedPort.external(A_ports[6]),
            ),
            # a_b_ext_out = {1'b0, 1'b1, b_out}
            ConstantConnection(
                source=ElaboratableValue("1'b0"),
                target=ReferencedPort(instance=inst_concat1, io=inst_concat1.module.ports[0]),
            ),
            ConstantConnection(
                source=ElaboratableValue("1'b1"),
                target=ReferencedPort(instance=inst_concat1, io=inst_concat1.module.ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_B, io=B.ports[1]),
                target=ReferencedPort(instance=inst_concat1, io=inst_concat1.module.ports[2]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_concat1, io=inst_concat1.module.ports[3]),
                target=ReferencedPort.external(A_ports[7]),
            ),
            # a_b_ext_bitsel_out = {{1'b0, b_out}, b_out}
            ConstantConnection(
                source=ElaboratableValue("1'b0"),
                target=ReferencedPort(instance=inst_concat2, io=inst_concat2.module.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_B, io=B.ports[1]),
                target=ReferencedPort(instance=inst_concat2, io=inst_concat2.module.ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_concat2, io=inst_concat2.module.ports[2]),
                target=ReferencedPort(instance=inst_concat3, io=inst_concat3.module.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_B, io=B.ports[1]),
                target=ReferencedPort(instance=inst_concat3, io=inst_concat3.module.ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_concat3, io=inst_concat3.module.ports[2]),
                target=ReferencedPort.external(A_ports[8]),
            ),
            # a_bit_sel_out = a_data_in[3]
            PortConnection(
                source=ReferencedPort.external(A_ports[3]),
                target=ReferencedPort(instance=inst_bitsel, io=inst_bitsel.module.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_bitsel, io=inst_bitsel.module.ports[1]),
                target=ReferencedPort.external(A_ports[9]),
            ),
            # a_range_sel_out = a_data_in[5:3]
            PortConnection(
                source=ReferencedPort.external(A_ports[3]),
                target=ReferencedPort(instance=inst_rangesel, io=inst_rangesel.module.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_rangesel, io=inst_rangesel.module.ports[1]),
                target=ReferencedPort.external(A_ports[10]),
            ),
            # selfdriven[0] = a_data_in[0]
            PortConnection(
                source=ReferencedPort.external(A_ports[3]),
                target=ReferencedPort(
                    instance=inst_bitsel_data0, io=inst_bitsel_data0.module.ports[0]
                ),
            ),
            # selfdriven[15] = ... = selfdriven[0] = a_data_in[0] (resolved through for loop chain)
            PortConnection(
                source=ReferencedPort(
                    instance=inst_bitsel_data0, io=inst_bitsel_data0.module.ports[1]
                ),
                target=ReferencedPort.external(A_ports[11]),
            ),
            # fordriven_out = {genfor_cinst#1.c_out, genfor_cinst#0.c_out}
            PortConnection(
                source=ReferencedPort(instance=inst_genfor_C1, io=C.ports[1]),
                target=ReferencedPort(instance=inst_concat4, io=inst_concat4.module.ports[0]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_genfor_C0, io=C.ports[1]),
                target=ReferencedPort(instance=inst_concat4, io=inst_concat4.module.ports[1]),
            ),
            PortConnection(
                source=ReferencedPort(instance=inst_concat4, io=inst_concat4.module.ports[2]),
                target=ReferencedPort.external(A_ports[12]),
            ),
        ],
    ),
)
