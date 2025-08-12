# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import itertools
import logging
from collections import Counter
from dataclasses import dataclass, field
from math import exp
from typing import Callable, Iterable, Iterator, Optional, cast

from pygtrie import CharTrie

from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import (
    BitStruct,
    LogicArray,
)
from topwrap.model.inference.mapping import InterfacePortGrouping, InterfacePortMapping
from topwrap.model.inference.port import PortSelector, PortSelectorOp
from topwrap.model.interface import InterfaceDefinition, InterfaceMode, InterfaceSignal
from topwrap.model.misc import QuerableView
from topwrap.model.module import Module


def parse_grouping_hints(grouping_hints: list[str]) -> dict[str, list[str]]:
    """
    Parse user-facing grouping hints into a dictionary for :func:`infer_interfaces_from_module`.

    The incoming hints are stored as they are specified on the command line, in the form of:
    :code:`"old1,old2,...,oldN=new"`, and are parsed into dictionaries with entries like this:
    :code:`"new": ["old1", "old2", ..., "oldN"]`
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

            out[new_name] = old_names
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

    #: Points awarded to each character of the prefix.
    prefix_length_score: int = field(default=10)

    #: Points awarded for matching all required signals (applied proportionally).
    required_match_score: int = field(default=10)

    #: Points awarded for matching all optional signals (applied proportionally).
    optional_match_score: int = field(default=5)

    #: Points awarded for missing all required signals (applied proportionally).
    required_missing_score: int = field(default=-20)

    #: Points awarded for missing all optional signals (applied proportionally).
    optional_missing_score: int = field(default=-2)

    #: Leniency in penalty for unmatched ports in a group.
    #: Penalty is computed as :code:`-(exp(n/leniency) - 1)`, such that matching all ports yields 0
    #: points.
    unmatched_port_penalty_leniency: int = field(default=5)

    #: Candidate interfaces with score below or equal to this limit will be ignored.
    score_lower_limit: int = field(default=0)


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
    _grouping_hints: dict[str, str],
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
                if port.name in _grouping_hints:
                    _grouping_hints[f"{port.name}[{i}]"] = f"{_grouping_hints[port.name]}[{i}]"

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
    ports: dict[str, PortSelector],
    grouping_hints: dict[str, list[str]],
    options: InterfaceInferenceOptions,
) -> dict[str, dict[str, PortSelector]]:
    """
    Generate candidate groups for interface instances.
    """

    _grouping_hints = {orig: new for new, names in grouping_hints.items() for orig in names}
    groups = {}

    for prefix, group in itertools.chain(
        _generate_struct_groups(module, _grouping_hints), _generate_prefix_groups(ports, options)
    ):
        # Check for any grouping hints that include this prefix.
        group_name = _grouping_hints.get(prefix, prefix)

        # Merge groups if one by the same name exists, as is the case when using grouping hints.
        if group_name in groups:
            groups[group_name].update(group)
        else:
            groups[group_name] = group

    # Also consider all ports as one big group.
    groups[""] = ports
    return groups


def _match_intf_signals_to_ports(
    ports: dict[str, PortSelector], intf: InterfaceDefinition
) -> dict[str, InterfaceSignal]:
    """
    Match port names to signals based on the signal regex patterns.
    """

    out = {}
    for sig in sorted(intf.signals, key=lambda v: len(v.name), reverse=True):
        for name in ports:
            if sig.regexp.match(name):
                out.update({name: sig})
                break

    return out


def _deduce_intf_mode_from_ports(
    module: Module,
    matched_ports: dict[str, InterfaceSignal],
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

    def _log_set(port_set: set[str], compare_dir: bool):
        for name in port_set:
            sig = matched_ports[name]
            sig_mode = sig.modes[InterfaceMode.MANAGER]
            port = ports[name]
            p_dir = module.ports.find_by_name_or_error(port.port).direction
            dir_comparison = (
                f" ({sig_mode.direction.value} != {p_dir.value})" if compare_dir else ""
            )
            logging.warning(f" - {sig.name} (port {str(port)}){dir_comparison}")

    if manager_count == subordinate_count:
        logging.warning(
            f"Unable to infer mode for candidate interface {intf.id.name}. There is an equal "
            "amount of manager and subordinate ports."
        )
        logging.warning("Manager ports:")
        _log_set(manager_set, False)
        logging.warning("Subordinate ports:")
        _log_set(manager_set, False)
        return None
    elif manager_count > subordinate_count:
        if subordinate_count > 0:
            logging.warning(
                f"Interface {intf.id.name} was deduced to be a manager interface, but the "
                f"following signals have the wrong direction:"
            )
            _log_set(subordinate_set, True)
        return InterfaceMode.MANAGER
    else:
        if manager_count > 0:
            logging.warning(
                f"Interface {intf.id.name} was deduced to be a subordinate interface, but the "
                f"following signals have the wrong direction:"
            )
            _log_set(manager_set, True)
        return InterfaceMode.SUBORDINATE


def _score_matched_intf_signals(
    matched_ports: dict[str, InterfaceSignal],
    ports: dict[str, PortSelector],
    mode: InterfaceMode,
    intf: InterfaceDefinition,
    options: InterfaceInferenceOptions,
) -> float:
    """
    Assign a score to the given candidate interface assignment based on the number of matched
    and unmatched signals and ports.
    """

    req_signals = {sig._id: False for sig in intf.signals if sig.modes[mode].required}
    opt_signals = {sig._id: False for sig in intf.signals if not sig.modes[mode].required}

    used_ports = set()
    for name, port in matched_ports.items():
        if port._id in req_signals:
            req_signals[port._id] = True
            used_ports.add(name)
        elif port._id in opt_signals:
            opt_signals[port._id] = True
            used_ports.add(name)

    unmatched_ports = {name: port for name, port in ports.items() if name not in used_ports}

    matched_req = sum([1 for x in req_signals.values() if x])
    matched_opt = sum([1 for x in opt_signals.values() if x])

    unmatched_req = sum([1 for x in req_signals.values() if not x])
    unmatched_opt = sum([1 for x in opt_signals.values() if not x])
    unmatched_ports = sum([1 for x in ports.keys() if x not in used_ports])

    return (
        (matched_req / len(intf.signals)) * options.required_match_score
        + (matched_opt / len(intf.signals)) * options.optional_match_score
        + (unmatched_req / len(intf.signals)) * options.required_missing_score
        + (unmatched_opt / len(intf.signals)) * options.optional_missing_score
        - (exp(unmatched_ports / options.unmatched_port_penalty_leniency) - 1)
    )


def infer_interfaces_from_module(
    module: Module,
    intf_defs: Iterable[InterfaceDefinition],
    grouping_hints: Optional[dict[str, list[str]]] = None,
    options: Optional[InterfaceInferenceOptions] = None,
) -> InterfacePortMapping:
    """
    Perform interface inference. Yields a mapping that can be applied using
    :func:`map_interfaces_to_module`.

    :param module: Module to perform inference on.
    :param intf_defs: Interface definitions to consider.
    :param grouping_hints: Hints for merging discovered groups into one.
    :param options: Configuration options for inference.
    """

    ports = {
        _drop_io_prefix(port, module.ports): PortSelector(port.name, ())
        for port in module.non_intf_ports()
        if not isinstance(port.type, BitStruct)
    }
    intf_defs = intf_defs
    options = options or InterfaceInferenceOptions()
    groups = _generate_candidate_groups(module, ports, grouping_hints or {}, options)
    candidates = []

    for group in groups.items():
        group_prefix, group_ports = group

        for intf in intf_defs:
            matched_ports = _match_intf_signals_to_ports(group_ports, intf)

            # If we didn't match anything, ignore this interface.
            if len(matched_ports) == 0:
                logging.debug(
                    f"Group '{group}' (definition {intf.id.name}) in module "
                    f"{module.id.name} has no matching ports, skipping."
                )
                continue

            mode = _deduce_intf_mode_from_ports(module, matched_ports, group_ports, intf)

            # If the ports don't fit into the interface's manager/subordinate signal directions,
            # ignore it.
            if not mode:
                continue

            # Prefer longer prefixes.
            score = len(group_prefix) * options.prefix_length_score
            score += _score_matched_intf_signals(matched_ports, group_ports, mode, intf, options)

            candidates.append((group_prefix, matched_ports, mode, intf, score))

    used_signals = set()
    out_groups = dict()
    used_names = Counter([x.name for x in module.interfaces])
    for prefix, matched, mode, intf_def, score in sorted(
        candidates, key=lambda v: v[-1], reverse=True
    ):
        name = prefix or intf_def.id.name

        logging.debug(
            f"Candidate interface {name} (definition {intf_def.id.name}) in module "
            f"{module.id.name} has score {score:.3f}"
        )

        if score <= options.score_lower_limit:
            # Since the list is sorted in descending order, we know nothing better can come
            # after this candidate.
            break

        any_used_signals = False
        for name, port in groups[prefix].items():
            if str(port) in used_signals:
                logging.info(
                    f"Interface {intf_def.id} not considered for prefix {prefix}, deduced port "
                    f"{str(port)} ({name}) already in use by higher scoring match"
                )
                any_used_signals = True
                break

        if any_used_signals:
            continue

        name = prefix or intf_def.id.name

        times_used = used_names[name]
        if times_used > 0:
            name = f"{name}_{times_used}"

        used_names.update([name])

        group = InterfacePortGrouping(
            interface=intf_def.id,
            mode=mode.name,
            signals={sig.name: groups[prefix][name] for name, sig in matched.items()},
        )

        logging.info(
            f"Inferred interface {name} (definition {intf_def.id.name}) in module {module.id.name}"
        )
        out_groups[name] = group

        for port in groups[prefix].values():
            used_signals.add(str(port))

    return InterfacePortMapping(
        id=module.id,
        interfaces=out_groups,
    )
