# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import itertools
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Collection, Iterable, Iterator, Optional, cast

from pygtrie import CharTrie

from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import (
    BitStruct,
    LogicArray,
    LogicBitSelect,
)
from topwrap.model.inference.port import PortSelector, PortSelectorOp
from topwrap.model.interface import Interface, InterfaceDefinition, InterfaceMode, InterfaceSignal
from topwrap.model.misc import QuerableView
from topwrap.model.module import Module


def parse_grouping_hints(grouping_hints: Iterable[str]) -> dict[str, str]:
    """
    Parse user-facing grouping hints into a dictionary for :func:`infer_interfaces_from_module`.

    The incoming hints are stored as they are specified on the command line, in the form of:
    :code:`"old1,old2,...,oldN=new"`, and are parsed into dictionaries with entries like this:
    :code:`{ "old1": "new", "old2": "new", ..., "oldN": "new" }`
    """

    out = {}

    for hint in grouping_hints:
        try:
            old_names, new_name = [x.strip() for x in hint.split("=")]
            old_names = [x.strip() for x in old_names.split(",")]

            if not new_name:
                raise ValueError("New group name cannot be empty")
            if any(not x for x in old_names):
                raise ValueError("Old group name cannot be empty")

            for old_name in old_names:
                out[old_name] = new_name
        except ValueError as e:
            raise ValueError(f"Invalid grouping hint syntax: '{hint}'") from e

    return out


@dataclass
class InterfaceInferenceOptions:
    """
    Configuration options for :func:`infer_interfaces_from_module`.
    """

    #: Minimum number of ports that must be in a group for it to be considered.
    min_group_size: int = field(default=2)

    #: Tokens on which prefixes are split on.
    prefix_split_tokens: list[str] = field(default_factory=lambda: ["_"])

    #: Should camel case prefixes be considered.
    prefix_consider_camel_case: bool = field(default=True)


TriePath = tuple[str, ...]
TrieChildResult = tuple[str, list[str]]


def _drop_io_prefix(port: Port, all_ports: QuerableView[Port]) -> str:
    """
    Given a port with an :code:`i_`, :code:`o_`, or :code:`io_` prefix, return a new name for it,
    with the prefix transformed into a suffix, while avoiding collisions with other port names.
    """

    prefixes = {
        "i_": PortDirection.IN,
        "o_": PortDirection.OUT,
        "io_": PortDirection.INOUT,
    }
    for prefix, direction in prefixes.items():
        if (
            port.name.startswith(prefix)
            and len(port.name) > len(prefix)
            and port.direction == direction
        ):
            new_name = f"{port.name.removeprefix(prefix)}_{prefix[:-1]}"
            # Check if the new candidate name collides with an existing port
            if all_ports.find_by_name(new_name):
                # Look for a port name that doesn't collide with anything
                ctr = 1
                while all_ports.find_by_name(f"{new_name}_{ctr}"):
                    ctr += 1
                new_name = f"{new_name}_{ctr}"
            return new_name
    return port.name


def _generate_port_list(module: Module) -> dict[str, PortSelector]:
    return {
        _drop_io_prefix(port, module.ports): PortSelector(port.name, ())
        for port in module.non_intf_ports()
        if not isinstance(port.type, BitStruct)
    }


def _process_bit_struct(
    parent: PortSelector, pfx: str, struct: BitStruct
) -> dict[str, PortSelector]:
    """
    Recursively generate group members from the given struct's fields.
    """
    out = {}

    for fld in struct.fields:
        field_sel = PortSelector(
            parent.port, tuple(list(parent.ops) + [(PortSelectorOp.FIELD, fld.field_name)])
        )

        if isinstance(fld.type, BitStruct):
            out.update(_process_bit_struct(field_sel, pfx, fld.type))
        else:
            out[str(field_sel).removeprefix(pfx)] = field_sel

    return out


def _generate_struct_groups(
    module: Module,
    grouping_hints: dict[str, str],
) -> Iterator[tuple[str, dict[str, PortSelector]]]:
    """
    Generate groups based on port struct members.
    """

    for port in module.non_intf_ports():
        if isinstance(port.type, LogicArray) and isinstance(port.type.item, BitStruct):
            if len(port.type.dimensions) != 1:
                logging.debug(
                    f"Port {port.name} is a multi-dimensional array of structs, ignoring."
                )
                continue

            try:
                lbound = int(port.type.dimensions[0].lower.value)
                ubound = int(port.type.dimensions[0].upper.value)
            except ValueError:
                logging.debug(
                    f"Port {port.name} has non-integer bounds ["
                    f"{int(port.type.dimensions[0].upper.value)}:"
                    f"{port.type.dimensions[0].lower.value}], ignoring."
                )
                continue

            for i in range(lbound, ubound + 1):
                if port.name in grouping_hints:
                    grouping_hints[f"{port.name}[{i}]"] = f"{grouping_hints[port.name]}[{i}]"

                sel = PortSelector(port.name, ((PortSelectorOp.SLICE, (i, i)),))
                yield (
                    f"{port.name}[{i}]",
                    _process_bit_struct(sel, f"{port.name}[{i}].", port.type.item),
                )
        elif isinstance(port.type, BitStruct):
            sel = PortSelector(port.name, ())
            yield (port.name, _process_bit_struct(sel, f"{port.name}.", port.type))


def _is_valid_prefix(options: InterfaceInferenceOptions, prefix: str, next_prefix: str) -> bool:
    """
    Checks validity of a prefix. A prefix is valid when:
     - the next character after it is one of the splitting tokens,
     - the last character of the prefix is lowercase, and the next character after it is
       uppercase (that is, the prefix is at a camel case word boundary).
    """

    if next_prefix[-1] in options.prefix_split_tokens:
        return True
    return options.prefix_consider_camel_case and (
        len(prefix) > 0
        and (
            (
                prefix[-1].islower()
                and (
                    next_prefix[-1].isupper() or next_prefix[-1].isdigit() or next_prefix[-1] == "_"
                )
            )
            or (
                (prefix[-1].islower() or prefix[-1].isdigit() or prefix[-1] == "_")
                and (next_prefix[-1].isupper())
            )
        )
    )


def _generate_prefix_groups(
    ports: dict[str, PortSelector],
    options: InterfaceInferenceOptions,
) -> Iterator[tuple[str, dict[str, PortSelector]]]:
    """
    Generate groups based on common prefixes.
    """

    def _traverse_callback(
        path_conv: Callable[[TriePath], str],
        path: TriePath,
        children: Iterable[TrieChildResult],
        _unused: None = None,
    ) -> TrieChildResult:
        """
        Traverses the trie, and, for each subtree, returns:
         - the prefix of the subtree,
         - the list of valid prefixes in the subtree.
        """
        valid_prefixes = []
        path_str = path_conv(path)

        for imm_child, prefixes in children:
            if _is_valid_prefix(options, path_str, imm_child):
                valid_prefixes.append(path_str)
            valid_prefixes += prefixes

        return path_str, valid_prefixes

    trie = CharTrie.fromkeys(ports.keys())

    _, prefixes = trie.traverse(_traverse_callback)

    for prefix in prefixes:
        keys = cast(list[str], trie.keys(prefix))
        group = {
            key.removeprefix(prefix).lstrip("".join(options.prefix_split_tokens)): ports[key]
            for key in keys
        }

        if len(group) < options.min_group_size:
            continue

        yield (prefix, group)


def _generate_candidate_groups(
    module: Module,
    grouping_hints: dict[str, str],
    options: InterfaceInferenceOptions,
) -> list[tuple[str, dict[str, PortSelector]]]:
    """
    Generate candidate groups for interface instances.
    """

    ports = _generate_port_list(module)
    groups = {}

    for prefix, group in itertools.chain(
        _generate_struct_groups(module, grouping_hints), _generate_prefix_groups(ports, options)
    ):
        # Check for any grouping hints that include this prefix.
        group_name = grouping_hints.get(prefix, prefix)

        # Merge groups if one by the same name exists, as is the case when using grouping hints.
        if group_name in groups:
            groups[group_name].update(group)
        else:
            groups[group_name] = group

    # Also consider all ports as one big group.
    groups[""] = ports

    return sorted(
        groups.items(),
        key=lambda group: len(group[0]),
        reverse=True,
    )


def _match_intf_signals_to_ports(
    ports: dict[str, PortSelector], intf: InterfaceDefinition
) -> dict[str, InterfaceSignal]:
    """
    Match port names to signals based on the signal regex patterns.
    """

    avail_names = list(sorted(ports, key=lambda n: (len(n), n)))
    out = {}

    for sig in sorted(intf.signals, key=lambda v: len(v.name), reverse=True):
        for name in avail_names:
            if sig.regexp.search(name.lower()):
                out.update({name: sig})
                avail_names.remove(name)
                break

    return out


def _deduce_intf_mode_from_ports(
    module: Module,
    matched_ports: dict[str, InterfaceSignal],
    name: str,
    ports: dict[str, PortSelector],
    intf: InterfaceDefinition,
) -> Optional[InterfaceMode]:
    """
    Determine the mode of the interface based on the directions of ports assigned to signals.
    """

    manager_set = set()
    subordinate_set = set()

    for name, sig in matched_ports.items():
        port = ports[name]
        p_dir = module.ports.find_by_name_or_error(port.port).direction

        m_dir = sig.modes[InterfaceMode.MANAGER].direction
        s_dir = sig.modes[InterfaceMode.SUBORDINATE].direction

        # Port matches both, so we cannot infer the mode based on it.
        # E.g. HREADY in AHB.
        if p_dir == m_dir and p_dir == s_dir:
            pass
        elif p_dir == m_dir:
            manager_set.add(name)
        elif p_dir == s_dir:
            subordinate_set.add(name)
        else:
            logging.warning(
                f"Port {str(port)} does not match any mode of signal {sig.name} of "
                f"interface {intf.id.name}"
            )
            return None

    manager_count = len(manager_set)
    subordinate_count = len(subordinate_set)

    def _log_set(port_set: set[str], deduced_mode: Optional[InterfaceMode]):
        for name in port_set:
            sig = matched_ports[name]
            port = ports[name]
            dir_comparison = ""
            if deduced_mode is not None:
                sig_mode = sig.modes[deduced_mode]
                p_dir = module.ports.find_by_name_or_error(port.port).direction
                dir_comparison = f" ({sig_mode.direction.value} != {p_dir.value})"
            logging.warning(f" - {sig.name} (port {str(port)}){dir_comparison}")

    if manager_count == subordinate_count:
        logging.warning(
            f"Unable to infer mode for candidate interface {name} (definition {intf.id.name}). "
            "There is an equal amount of manager and subordinate ports."
        )
        logging.warning("Manager ports:")
        _log_set(manager_set, None)
        logging.warning("Subordinate ports:")
        _log_set(subordinate_set, None)
        return None
    elif manager_count > subordinate_count:
        if subordinate_count > 0:
            logging.warning(
                f"Interface {name} (definition {intf.id.name}) was deduced to likely be a manager"
                " interface, but the following signals have the wrong direction:"
            )
            _log_set(subordinate_set, InterfaceMode.MANAGER)
            return None
        return InterfaceMode.MANAGER
    else:
        if manager_count > 0:
            logging.warning(
                f"Interface {name} (definition {intf.id.name}) was deduced to likely be a "
                "subordinate interface, but the following signals have the wrong direction:"
            )
            _log_set(manager_set, InterfaceMode.SUBORDINATE)
            return None
        return InterfaceMode.SUBORDINATE


def _candidate_interfaces_for_group(
    group: tuple[str, dict[str, PortSelector]],
    grouping_hints: dict[str, str],
    module: Module,
    intf_defs: Collection[InterfaceDefinition],
) -> Iterable[Interface]:
    """
    For a given group, generate candidate interfaces that can be created from the group.
    """

    prefix, ports = group

    for intf in intf_defs:
        m_req_signals = {
            sig._id for sig in intf.signals if sig.modes[InterfaceMode.MANAGER].required
        }
        s_req_signals = {
            sig._id for sig in intf.signals if sig.modes[InterfaceMode.SUBORDINATE].required
        }
        min_matching = min(len(m_req_signals), len(s_req_signals))

        name = prefix or grouping_hints.get(intf.id.name) or intf.id.name

        matched_ports = _match_intf_signals_to_ports(ports, intf)

        # If the amount of ports is less than the minimum amount of required signals, ignore it.
        if len(matched_ports) < min_matching:
            continue

        mode = _deduce_intf_mode_from_ports(module, matched_ports, name, ports, intf)

        # If the ports don't fit into the interface's signal directions, ignore it.
        if not mode:
            continue

        # If the matched ports do not contain all required signals of the interface, ignore it.
        matched_sigs = {sig._id for sig in matched_ports.values()}
        required_sigs = {sig._id for sig in intf.signals if sig.modes[mode].required}
        if required_sigs.intersection(matched_sigs) != required_sigs:
            continue

        intf = Interface(
            name=name,
            mode=mode,
            definition=intf,
            signals={
                sig._id: ports[pname].make_referenced_port(module, mode, sig)
                for pname, sig in matched_ports.items()
            },
        )
        yield intf


def _candidate_intf_ordering_key(candidate: Interface) -> tuple[int, int]:
    """
    Generate a sorting key for a given candidate.
    """

    cand_def = candidate.definition
    mode = candidate.mode

    cand_signals = set(candidate.signals)

    req_signals = {sig._id for sig in cand_def.signals if sig.modes[mode].required}
    opt_signals = {sig._id for sig in cand_def.signals if not sig.modes[mode].required}

    return (
        # First, prefer interfaces with more required signals.
        # We know all of these have been matched.
        len(req_signals),
        # Secondly, prefer interfaces with more optional signals matched.
        len(opt_signals.intersection(cand_signals)),
    )


def _intf_used_ports(intf: Interface) -> set[str]:
    out = set()

    for ref in intf.signals.values():
        if ref is None:
            continue

        if isinstance(ref.io.type, LogicArray) and isinstance(ref.io.type.item, BitStruct):
            # Append the index to the port name
            assert len(ref.select.ops) > 0, "No select for LogicArray"
            slice_op = ref.select.ops[0]
            assert isinstance(slice_op, LogicBitSelect), "No slice for LogicArray"
            slice_dim = slice_op.slice
            assert slice_dim.lower == slice_dim.upper, "Slicing multiple structs"

            out.add(f"{ref.io.name}[{slice_dim.lower}]")
        else:
            # Here we assume a single struct is used only for a single interface.
            # That is, we don't support foo.axi1, foo.axi2, ...
            out.add(ref.io.name)

    return out


def infer_interfaces_from_module(
    module: Module,
    intf_defs: Collection[InterfaceDefinition],
    grouping_hints: Optional[dict[str, str]] = None,
    options: Optional[InterfaceInferenceOptions] = None,
):
    """
    Perform interface inference. Attempts to infer interfaces that the given module contains, and
    adds them to the module.

    :param module: Module to perform inference on.
    :param intf_defs: Interface definitions to consider.
    :param grouping_hints: Hints for merging discovered groups into one.
    :param options: Configuration options for inference.
    """

    options = options or InterfaceInferenceOptions()
    grouping_hints = grouping_hints or {}

    groups = _generate_candidate_groups(module, grouping_hints, options)

    candidates = list[Interface]()
    for group in groups:
        group_cand = sorted(
            _candidate_interfaces_for_group(group, grouping_hints, module, intf_defs),
            key=_candidate_intf_ordering_key,
            reverse=True,
        )
        candidates.extend(group_cand)

    used_ports = set()
    for intf in module.interfaces:
        used_ports |= _intf_used_ports(intf)
    used_names = Counter([x.name for x in module.interfaces])
    for candidate in candidates:
        cand_def = candidate.definition
        cand_ports = _intf_used_ports(candidate)
        # If the set of ports used by the candidate interface overlaps the set of used ports,
        # ignore this candidate.
        if cand_ports.intersection(used_ports):
            logging.info(
                f"Candidate interface {candidate.name} (definition {cand_def.id}) "
                "ignored: set of ports overlaps ports used by other interface(s)"
            )
            continue

        used_ports |= cand_ports

        name = candidate.name
        if name in used_names:
            name = f"{name}_{used_names[name]}"
        used_names.update([name])
        candidate.name = name

        module.add_interface(candidate)

        logging.info(f"Inferred interface {name} (definition {cand_def.id}) in module {module.id}")
