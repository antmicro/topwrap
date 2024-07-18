# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import json
import subprocess
import tempfile
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from logging import warning
from math import exp
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Set, Tuple

from pygtrie import CharTrie
from typing_extensions import override

from .hdl_parsers_utils import PortDefinition
from .interface import (
    IfacePortSpecification,
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignalType,
    get_interfaces,
)


@dataclass(frozen=True)
class InterfaceMatch:
    """Describes a potential matching between ports in an RTL source and abstract
    signals of an interface"""

    signals: Dict[IfacePortSpecification, PortDefinition]
    bus_type: str
    name: str
    mode: InterfaceMode


class SignalGrouper(ABC):
    """Abstract class for separating ports into disjunctive groups according to some criteria."""

    @abstractmethod
    def group(self, ports: Set[PortDefinition]) -> Dict[str, Set[PortDefinition]]:
        """
        Splits `ports` into groups distinguished by a string.

        :param ports: Ports to be grouped
        :return: Mapping from strings to disjoint subsets of `ports`.
        Some ports in `ports` may not belong to any subset.
        """
        pass


class EmptyGrouper(SignalGrouper):
    """Port grouping class that doesn't perform any grouping at all"""

    def group(self, ports: Set[PortDefinition]) -> Dict[str, Set[PortDefinition]]:
        return {}


class GrouperByPrefix(SignalGrouper):
    """Port grouping class that groups them by user-supplied iterable of port name prefixes"""

    def __init__(self, prefixes: Iterable[str]):
        self._prefixes = prefixes

    @override
    def group(self, ports: Set[PortDefinition]) -> Dict[str, Set[PortDefinition]]:
        iface_mappings = {}

        for prefix in self._prefixes:
            iface_matches = set(filter(lambda port: port.name.startswith(prefix), ports))
            if iface_matches:
                iface_mappings[prefix] = iface_matches
            else:
                warning(f"found no matching ports for interface with prefix '{prefix}'")

        return iface_mappings


class GrouperByPrefixAuto(SignalGrouper):
    """Port grouping class that groups them by autodetected prefixes in signal names"""

    def __init__(self, *, min_prefix_occurences: int = 3, split_tokens: Set[str] = set(["_"])):
        """
        :param min_prefix_occurences: minimum number of signal names with a given prefix for
        their prefix to be considered valid
        :param split_tokens: set of strings considered as valid separators for signal name
        """
        self._min_prefix_occurences = min_prefix_occurences
        self._split_tokens = split_tokens

    def _is_valid_prefix(self, occurences_count, prefix, next_prefix):
        """
        Checks validity of a prefix. A prefix is defined as valid when:
        - there are enough strings with a given prefix AND
          - first character after a prefix is one of the splitting tokens ("_" by default) OR
          - last character of a prefix is lowercase and subsequent character is uppercase (as in camelCase)
        """
        return occurences_count >= self._min_prefix_occurences and (
            next_prefix[-1] in self._split_tokens
            or (len(prefix) > 0 and prefix[-1].islower() and next_prefix[-1].isupper())
        )

    @override
    def group(self, ports: Set[PortDefinition]) -> Dict[str, Set[PortDefinition]]:
        TriePath = Tuple[str, ...]
        TriePathConvFunction = Callable[[TriePath], str]
        TrieChildResult = Tuple[int, str, List[str]]

        def traverse_callback(
            path_conv: TriePathConvFunction,
            path: TriePath,
            children: Iterable[TrieChildResult],
            is_leaf: bool = False,
        ) -> TrieChildResult:
            """
            Traverses a trie and returns, for each subtree:
            - leaf count under the subtree
            - prefix of the subtree
            - list of valid prefixes in the subtree (strings split by either a char in self.split_tokens or camelCase)
            """
            leaves = 1 if is_leaf else 0
            valid_prefixes = []
            path_str = path_conv(path)

            # iterating over the children also calls traverse_callback on them and
            # iterated values are what it returned
            for leaf_count, imm_child, prefixes in children:
                if self._is_valid_prefix(leaf_count, path_str, imm_child):
                    valid_prefixes.append(path_str)
                valid_prefixes += prefixes
                leaves += leaf_count

            return leaves, path_str, valid_prefixes

        prefix_map = defaultdict(set)
        name_map = {port.name: port for port in ports}
        trie = CharTrie.fromkeys(name_map.keys(), value=True)

        _, _, prefixes = trie.traverse(traverse_callback)
        # iterate prefixes from longest to shortest
        for prefix in sorted(prefixes, reverse=True):
            if trie.has_subtrie(prefix):
                # get all signals with a prefix and remove their names from
                # the trie to not consider them later for shorter prefixes
                for key in trie.keys(prefix):
                    prefix_map[prefix.rstrip("_")].add(name_map[key])
                    trie.pop(key)

        return prefix_map


class GrouperByAttribute(SignalGrouper):
    """Groups ports by their "interface" attribute with yosys"""

    def __init__(self, hdl_file: str):
        self.hdl_file = hdl_file

    @override
    def group(self, ports: Set[PortDefinition]) -> Dict[str, Set[PortDefinition]]:
        """
        Based on attributes in RTL source (in file self.hdl_file) in the form of:
        (* interface="interface_name" *)
        output[31:0] some_output;
        (* interface="interface_name" *)
        input[15:0] some_input;

        returns a dict in the form of:
        {
            "interface_name": [
                PortDefinition(
                    name = "some_output",
                    direction = PortDirection.OUT,
                    upper_bound = "31"
                    lower_bound = "0",
                ),
                PortDefinition(
                    name = "some_input",
                    direction = PortDirection.IN,
                    upper_bound = "15",
                    lower_bound = "0",
                )
            ]
        }
        """

        with tempfile.NamedTemporaryFile() as json_file:
            subprocess.check_output(
                [
                    "yosys",
                    "-p",
                    f"read_verilog {self.hdl_file}",
                    "-p",
                    "proc",
                    "-p",
                    f"write_json {json_file.name}",
                ]
            )

            contents = json_file.read()
            modules = json.loads(contents)["modules"]
            interfaces = defaultdict(set)
            ports_by_name = {port.name: port for port in ports}

            try:
                # TODO handle multiple modules
                module_name, module = modules.popitem()
                for name, port in module["netnames"].items():
                    attrs = port["attributes"]
                    if "interface" in attrs:
                        iface = attrs["interface"]
                        interfaces[iface].add(ports_by_name[name])
            except KeyError:
                pass

            return dict(interfaces)


class InterfaceMatcher(ABC):
    """
    Abstract class for performing matching of a set of RTL ports to a set of abstract
    interface ports.
    """

    @abstractmethod
    def match(
        self, iface_signals: Set[IfacePortSpecification], signals: Set[PortDefinition]
    ) -> Dict[IfacePortSpecification, PortDefinition]:
        """
        For some set of interface signals (that are abstract - they only exist as
        part of an interface specification) and some set of signal instances
        (that are concrete - they exist in the RTL source) this method pairs
        interface signals with signal instances. Some interface signals and
        signal instances may not get paired.

        :param iface_signals: interface signals
        :param signals: signal instances
        :return: Pairing of interface signals and signal instances
        """
        pass


class RegexInterfaceMatcher(InterfaceMatcher):
    """Matches ports based on a regexp describing abstract interface port name"""

    @override
    def match(
        self, iface_signals: Set[IfacePortSpecification], signals: Set[PortDefinition]
    ) -> Dict[IfacePortSpecification, PortDefinition]:
        """
        Tries to match signal names from RTL to signal names (specified as regexps)
        in interface specification.
        """
        matched = {}
        remaining_sigs = signals.copy()
        # iterate from the longest to shortest signal name (to prevent e.g. "RID" interface signal
        # name being matched with "ARID" RTL signal name)
        for iface_signal in sorted(iface_signals, key=lambda v: len(v.name), reverse=True):
            for port_def in remaining_sigs:
                if iface_signal.regexp.search(port_def.name.lower()):
                    matched[iface_signal] = port_def
                    remaining_sigs.remove(port_def)
                    break
        return matched


class InterfaceMatchScorer(ABC):
    """
    Abstract class for computing a score of how well a set of RTL ports matches
    set of abstract signals in an interface.
    """

    @abstractmethod
    def score(
        self,
        iface_spec: InterfaceDefinition,
        signals: Set[PortDefinition],
        matched_signals: Dict[IfacePortSpecification, PortDefinition],
    ) -> float:
        """
        Compute score that evaluates how well a set of signals matches the specification
        of an interface.

        :param iface_spec: interface definition (typically from YAML interface description)
        :param signals: overall set of signals that are supposed to be part of this interface
        :param matched_signals: pairing of signals from `iface_spec.signals` and `signals`. Note
        that not all elements from `iface_spec.signals` and `signals` have to be paired with each other.
        """
        pass


class InterfaceMatchGroupScorer(InterfaceMatchScorer):
    """
    Computes a score for an interface match based on:
    - the amount of required and optional abstract interface
      signals matched and not matched
    - the amount of signals in a group of signals left unmatched
    """

    def __init__(
        self,
        *,
        match_required_points: int = 10,
        missing_required_points: int = -20,
        match_optional_points: int = 5,
        missing_optional_points: int = -2,
    ):
        """
        :param match_required_points: weighted coefficient (meaning a percentage of
        matched required signals * this value is the will be the resulting score)
        for matching required signals
        :param missing_required_points: weighted coefficient for not matching required signals
        :param match_optional_points: weighted coefficient for matching optional signals
        :param missing_optional_points: weighted coefficient for not matching optional signals
        """
        self._match_required_points = match_required_points
        self._missing_required_points = missing_required_points
        self._match_optional_points = match_optional_points
        self._missing_optional_points = missing_optional_points

    @override
    def score(
        self,
        iface_spec: InterfaceDefinition,
        signals: Set[PortDefinition],
        matched_signals: Dict[IfacePortSpecification, PortDefinition],
    ) -> float:
        def score_for_group(len_sigs_matched, len_sigs_in_iface, match_points, missing_points):
            unmatched_sigs_in_iface = len_sigs_in_iface - len_sigs_matched
            if len_sigs_in_iface != 0:
                score_matched = (len_sigs_matched / len_sigs_in_iface) * match_points
                score_missing = (unmatched_sigs_in_iface / len_sigs_in_iface) * missing_points
                return score_matched + score_missing
            else:
                return 0

        matched_req = list(
            filter(lambda k: k.type == InterfaceSignalType.REQUIRED, matched_signals.keys())
        )
        matched_opt = list(
            filter(lambda k: k.type == InterfaceSignalType.OPTIONAL, matched_signals.keys())
        )

        score_req = score_for_group(
            len(matched_req),
            len(iface_spec.required_signals),
            self._match_required_points,
            self._missing_required_points,
        )
        score_opt = score_for_group(
            len(matched_opt),
            len(iface_spec.optional_signals),
            self._match_optional_points,
            self._missing_optional_points,
        )

        unmatched_cnt = len(signals) - len(matched_signals)
        # penalize not matching all signals in a given group
        # baseline for this value is 0 when all signals in the group have been
        # matched (since exp(0) + 1 = 0), whereas for each signal that wasn't this
        # value decreases exponentially, thus overall preferring interfaces that
        # have matched more signals from a group
        unmatched_penalty = -exp(unmatched_cnt / 5) + 1

        return score_req + score_opt + unmatched_penalty


class ModeDeducer(ABC):
    """
    Abstract class for deducing mode (master/slave) from a matching of abstract
    interface signals to RTL ports.
    """

    @abstractmethod
    def deduce_mode(
        self,
        iface_spec: InterfaceDefinition,
        matched_signals: Dict[IfacePortSpecification, PortDefinition],
    ) -> InterfaceMode:
        """
        Tries to infer interface mode (i.e. direction)

        :param iface_spec: interface specification
        :param matched_signals: pairing of interface signals to signal instances
        :return: mode of an interface (master/slave/unknown)
        """
        pass


class BasicModeDeducer(ModeDeducer):
    """Deduces interface mode based on the direction of some one representative signal."""

    @override
    def deduce_mode(
        self,
        iface_spec: InterfaceDefinition,
        matched_signals: Dict[IfacePortSpecification, PortDefinition],
    ) -> InterfaceMode:
        if matched_signals:
            # pick a representative from matched_signals and check it's direction against the one
            # in interface specification file - if it matches then it's a master since we assume
            # the specification to be from the master's perspective, otherwise it's a slave
            iface_sig, rtl_sig = list(matched_signals.items())[0]
            if iface_sig in iface_spec.signals and rtl_sig.direction == iface_sig.direction:
                return InterfaceMode.MASTER
            else:
                return InterfaceMode.SLAVE
        else:
            return InterfaceMode.UNSPECIFIED


class InterfaceGrouper(ABC):
    """
    Abstract class for representing the whole process of matching
    a set of RTL ports into interfaces.
    """

    def __init__(self, ifaces: Iterable[InterfaceDefinition]):
        self.ifaces = ifaces

    @abstractmethod
    def group_to_interfaces(self, ports: Set[PortDefinition]) -> Iterable[InterfaceMatch]:
        """
        Groups a set of ports of a module by their interface.
        Some ports can remain unmatched to an interface, but one port
        can only be part of one interface.

        :param ports: ports of an RTL module
        :return: iterable of InterfaceMatch objects describing an interface,
        including pairing of abstract interface signals from specification
        to concrete signal instances from the RTL source
        """
        pass


class Interface4StageGrouper(InterfaceGrouper):
    """
    Matches a set of RTL ports into interfaces in 4 stages:
    1. group a set of ports into disjoint sets based on some criteria
    for set in sets:
        for interface in interfaces:
            2. try to match ports in set to ports in interface
            3. deduce mode (master/slave) of the matched interface
            4. compute score for the matching
        choose best-scoring interface as the chosen interface for that set

    Implementation of all stages can be chosen independently.
    """

    def __init__(
        self,
        ifaces: Iterable[InterfaceDefinition],
        group_stage: SignalGrouper,
        match_stage: InterfaceMatcher,
        score_stage: InterfaceMatchScorer,
        mode_stage: ModeDeducer,
    ):
        super().__init__(ifaces)
        self._group_stage = group_stage
        self._match_stage = match_stage
        self._score_stage = score_stage
        self._mode_stage = mode_stage

    @override
    def group_to_interfaces(self, ports: Set[PortDefinition]) -> Iterable[InterfaceMatch]:
        def match_against_all_ifaces(iface_rtl_ports, iface_name):
            for iface in self.ifaces:
                match = self._match_stage.match(set(iface.signals), iface_rtl_ports)
                mode = self._mode_stage.deduce_mode(iface, match)
                score = self._score_stage.score(iface, iface_rtl_ports, match)
                yield score, InterfaceMatch(
                    signals=match, bus_type=iface.name, name=iface_name, mode=mode
                )

        matched_ifaces = []
        for iface_name, iface_rtl_ports in self._group_stage.group(ports).items():
            matches = match_against_all_ifaces(iface_rtl_ports, iface_name)
            _, best_iface_match = max(matches, key=lambda t: t[0])  # select max by score
            # check if the match matched any signals at all - sometimes we'll select "best"
            # interface but with 0 signals matched because we're trying to match an unknown
            # interface against some known one
            if best_iface_match.signals:
                matched_ifaces.append(best_iface_match)

        return matched_ifaces


def standard_iface_grouper(
    hdl_filename: Path = Path(),
    use_yosys: bool = False,
    iface_deduce: bool = True,
    ifaces_names: tuple = (),
) -> InterfaceGrouper:
    """
    Factory method for constructing an interface grouper

    :param hdl_filename: path to the HDL file, only used when use_yosys is True
    :param use_yosys: use yosys to deduce interface names for grouping them
    :param iface_deduce: detect interface names automatically for grouping them
    :param ifaces_names: use a tuple of interface names for grouping them
    """
    signal_grouper = EmptyGrouper()
    if use_yosys:
        signal_grouper = GrouperByAttribute(hdl_filename)
    elif iface_deduce:
        signal_grouper = GrouperByPrefixAuto()
    elif ifaces_names:
        signal_grouper = GrouperByPrefix(ifaces_names)

    return Interface4StageGrouper(
        get_interfaces(),
        signal_grouper,
        RegexInterfaceMatcher(),
        InterfaceMatchGroupScorer(),
        BasicModeDeducer(),
    )
