# Copyright (c) 2026-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from tests.tests_ir.frontend.test_kpm_examples import _all_inst_params, _flatten_conns_to_dict
from topwrap.model.connections import (
    ConstantConnection,
    InterfaceConnection,
    PortConnection,
    PortDirection,
    ReferencedIO,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.interface import Interface
from topwrap.model.module import Module


def _module_non_intf_port_dict(module: Module) -> dict[str, PortDirection]:
    return {port.name: port.direction for port in module.non_intf_ports()}


def _compare_referenced_io(left: ReferencedIO, right: ReferencedIO):
    assert isinstance(left, ReferencedPort) == isinstance(right, ReferencedPort)
    assert left.io.name == right.io.name
    assert (left.instance is None) == (right.instance is None)
    if left.instance and right.instance:
        assert left.instance.name == right.instance.name


def _compare_ports(left: Design, right: Design):
    l_port_conns = [x for x in left.connections if isinstance(x, PortConnection)]
    r_port_conns = [x for x in right.connections if isinstance(x, PortConnection)]
    assert _flatten_conns_to_dict(l_port_conns) == _flatten_conns_to_dict(r_port_conns)

    l_if_conns = [x for x in left.connections if isinstance(x, InterfaceConnection)]
    r_if_conns = [x for x in right.connections if isinstance(x, InterfaceConnection)]
    assert _flatten_conns_to_dict(l_if_conns) == _flatten_conns_to_dict(r_if_conns)

    l_const_conns = [x for x in left.connections if isinstance(x, ConstantConnection)]
    r_const_conns = [x for x in right.connections if isinstance(x, ConstantConnection)]
    assert _flatten_conns_to_dict(l_const_conns) == _flatten_conns_to_dict(r_const_conns)


def _compare_interconnects(left: Design, right: Design):
    all_names = set(x.name for x in left.interconnects).union(
        set(x.name for x in right.interconnects)
    )
    l_interconnects = {x.name: x for x in left.interconnects}
    r_interconnects = {x.name: x for x in right.interconnects}

    for name in all_names:
        assert name in l_interconnects
        assert name in r_interconnects
        l_ic = l_interconnects[name]
        r_ic = r_interconnects[name]

        _compare_referenced_io(l_ic.clock, r_ic.clock)
        _compare_referenced_io(l_ic.reset, r_ic.reset)

        assert l_ic.params == r_ic.params

        all_man_names = set(x.resolve().io.name for x in l_ic.managers).union(
            set(x.resolve().io.name for x in r_ic.managers)
        )
        l_mans = {x.resolve().io.name: x.resolve() for x in l_ic.managers}
        r_mans = {x.resolve().io.name: x.resolve() for x in r_ic.managers}

        for name in all_man_names:
            assert name in l_mans
            assert name in r_mans
            l_man = l_mans[name]
            r_man = r_mans[name]

            assert l_ic.managers[l_man._id] == r_ic.managers[r_man._id]

            _compare_referenced_io(l_man, r_man)
            _compare_interface(l_man.io, r_man.io)

        all_sub_names = set(x.resolve().io.name for x in l_ic.subordinates).union(
            set(x.resolve().io.name for x in r_ic.subordinates)
        )
        l_subs = {x.resolve().io.name: x.resolve() for x in l_ic.subordinates}
        r_subs = {x.resolve().io.name: x.resolve() for x in r_ic.subordinates}

        for name in all_sub_names:
            assert name in l_subs
            assert name in r_subs
            l_sub = l_subs[name]
            r_sub = r_subs[name]

            assert l_ic.subordinates[l_sub._id] == r_ic.subordinates[r_sub._id]

            _compare_referenced_io(l_sub, r_sub)
            _compare_interface(l_sub.io, r_sub.io)


def _compare_designs(left: Design, right: Design):
    _compare_ports(left, right)
    _compare_interconnects(left, right)

    all_names = set(x.name for x in left.components).union(set(x.name for x in right.components))
    l_components = {x.name: x for x in left.components}
    r_components = {x.name: x for x in right.components}

    for name in all_names:
        assert name in l_components
        assert name in r_components
        _compare_module_inst(l_components[name], r_components[name])


def _compare_module_inst(left: ModuleInstance, right: ModuleInstance):
    assert _all_inst_params(left) == _all_inst_params(right)
    _compare_modules(left.module, right.module)


def _compare_interface(left: Interface, right: Interface):
    assert left.parent.id == right.parent.id
    assert left.name == right.name
    assert left.mode == right.mode
    assert left.definition == right.definition

    # Signal realization is not compared because the KPM spec and dataflow don't store that
    # information on their own.


def _compare_interfaces(left: Module, right: Module):
    all_names = set(x.name for x in left.interfaces).union(set(x.name for x in right.interfaces))
    l_intfs = {x.name: x for x in left.interfaces}
    r_intfs = {x.name: x for x in right.interfaces}

    for name in all_names:
        assert name in l_intfs
        assert name in r_intfs

        _compare_interface(l_intfs[name], r_intfs[name])


def _compare_clocks_resets(left: Module, right: Module):
    # Check for duplicate clock names
    l_clock_names = [clk.name for clk in left.clocks]
    r_clock_names = [clk.name for clk in right.clocks]

    assert len(l_clock_names) == len(set(r_clock_names))
    assert len(r_clock_names) == len(set(r_clock_names))

    # Check that clocks have the same ports
    assert set(left.clocks) == set(right.clocks)

    # Check for duplicate reset names
    l_reset_names = [rst.name for rst in left.resets]
    r_reset_names = [rst.name for rst in right.resets]

    assert len(l_reset_names) == len(set(l_reset_names))
    assert len(r_reset_names) == len(set(r_reset_names))

    # Check that clocks have the same ports
    assert set(left.resets) == set(right.resets)


def _compare_parameters(left: Module, right: Module):
    # Check for duplicate parameter names
    l_param_names = [param.name for param in left.parameters]
    r_param_names = [param.name for param in right.parameters]

    assert len(l_param_names) == len(set(l_param_names))
    assert len(r_param_names) == len(set(r_param_names))

    # Check that parameters are the same
    assert set(left.parameters) == set(right.parameters)


def _compare_modules(left: Module, right: Module, compare_designs: bool = True):
    assert left.id == right.id
    if compare_designs:
        assert (left.design is None) == (right.design is None)

    _compare_interfaces(left, right)

    assert _module_non_intf_port_dict(left) == _module_non_intf_port_dict(right)
    _compare_clocks_resets(left, right)

    if compare_designs:
        if left.design and right.design:
            _compare_designs(left.design, right.design)
