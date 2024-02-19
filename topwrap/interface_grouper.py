# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import functools
import importlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from logging import warning
from math import exp
from pathlib import Path
from typing import Dict, Iterable, List, Set, Union

from yaml import Loader, safe_load

from .hdl_parsers_utils import PortDefinition
from .util import removeprefix


@dataclass(frozen=True)
class InterfaceMatch:
    signals: Dict[str, PortDefinition]
    bus_type: str
    prefix: str


class InterfaceGrouper:
    """This class provides a possibility to group ports of a specific HDL file
    into different interfaces (e.g AXI, AXILite...).
    """

    def __init__(self, use_yosys: bool, iface_deduce: bool, ifaces_names: tuple):
        """Set config variables which determine, how to perform grouping."""
        self.use_yosys = use_yosys
        self.iface_deduce = iface_deduce
        self.ifaces_names = ifaces_names

    def __match_signals(
        self, sig_regexps: Dict[str, re.Pattern], signals: Set[PortDefinition], prefix: str
    ) -> Dict[str, PortDefinition]:
        """Tries to match signal names from RTL to signal names in interface specification"""
        matched = {}
        for iface_sig_name, regexp in sig_regexps.items():
            for port_def in signals:
                if regexp.search(removeprefix(port_def.name, prefix).lstrip("_")):
                    matched[iface_sig_name] = port_def
        return matched

    def __interface_matching_score(
        self,
        iface_spec: Dict[str, Union[str, Dict[str, Iterable[str]]]],
        signals: Set[PortDefinition],
        prefix: str,
    ) -> (int, Dict[str, PortDefinition]):
        """Compute score of how much a set of signals `signals` matches
        a specification of interface `iface_spec`

        :param iface_spec: interface YAML
        :param signals: set of signals as PortDefinitions
        :param prefix: common prefix of all signals
        """

        match_required_points = 10
        missing_required_points = -20
        match_optional_points = 5
        missing_optional_points = -2

        def score_for_group(signals_regexps, match_points, missing_points):
            signals_regexps_compiled = {
                k: re.compile(regexp) for k, regexp in signals_regexps.items()
            }
            matched = self.__match_signals(signals_regexps_compiled, signals, prefix)
            unmatched_iface_cnt = len(signals_regexps) - len(matched)
            if len(signals_regexps) != 0:
                score_matched = (len(matched) / len(signals_regexps)) * match_points
                score_missing = (unmatched_iface_cnt / len(signals_regexps)) * missing_points
                return score_matched + score_missing, matched
            else:
                return 0, matched

        score_req, matched_req = score_for_group(
            iface_spec["signals"]["required"] or {}, match_required_points, missing_required_points
        )
        score_opt, matched_opt = score_for_group(
            iface_spec["signals"]["optional"] or {}, match_optional_points, missing_optional_points
        )

        matched = {}
        matched.update(matched_req)
        matched.update(matched_opt)

        unmatched_cnt = len(signals) - len(matched)
        # penalize not matching all signals in an interface
        # baseline for this value is 0 when all signals with the prefix have been
        # matched (since exp(0) + 1 = 0), whereas for each signal that wasn't this
        # value decreases exponentially, thus overall preferring interfaces that
        # have matched more signals with identical prefix
        unmatched_penalty = -exp(unmatched_cnt / 5) + 1

        return score_req + score_opt + unmatched_penalty, matched

    def __find_common_prefix(self, ports: list):
        """Find a prefix that is the most common among ports names.

        :param ports: sorted list of ports names

        :return: (prefix, i, j) prefix, first and last index where the
            prefix occurs
        """

        # longest common prefix function
        def _lcp(str1: str, str2: str):
            for i in range(min(len(str1), len(str2))):
                if str1[i] != str2[i]:
                    break
            return str1[:i]

        # simple heuristic that is used to prefer less names with
        # longer prefixes than more names with shorter prefixes
        def _heuristic(pref_len: int, count: int, prefix: str, port: str):
            # forbid prefix that is not on word boundary. We assume words are
            # either separated by _ or lowercase letter followed by an uppercase letter
            # (as in camelCase)
            if prefix and (
                prefix[-1] != "_" or (prefix[-1].islower() and port.lstrip(prefix).islower())
            ):
                return -1
            return pref_len**3 * count

        lcp_prev = [1] + [0] * (len(ports) - 1)
        for i in range(1, len(ports)):
            lcp_prev[i] = len(_lcp(ports[i], ports[i - 1]))

        # dp_mins[i][j] - minimal value of lcp_prev[i:j+1]
        dp_mins = [[0 for _ in range(len(lcp_prev))] for _ in range(len(lcp_prev))]
        for i in range(len(lcp_prev)):
            for j in range(i, len(lcp_prev)):
                if i == j:
                    dp_mins[i][j] = lcp_prev[i]
                else:
                    dp_mins[i][j] = min(lcp_prev[j], dp_mins[i][j - 1])

        min_num_prefixes = 3  # don't consider prefixes that occur <=3 times
        min_heur_value = 10  # don't consider very short prefixes
        best_heur, best_prefix, best_i, best_j = 0, "", -1, -1
        # find prefix for which the heuristic value is the highest
        for i in range(len(lcp_prev)):
            for j in range(i + min_num_prefixes, len(lcp_prev)):
                prefix = ports[i][: dp_mins[i][j]]
                heur = _heuristic(dp_mins[i][j], j - i + 1, prefix, ports[i])
                if heur > best_heur and heur > min_heur_value:
                    best_i, best_j = i, j
                    best_heur, best_prefix = heur, prefix

        return (best_prefix.rstrip("_"), best_i - 1, best_j)

    def __create_interface_mappings(self, ifaces_names, ports):
        """Try to create interface mappings by matching given interfaces names
        with ports names prefixes

        :param ports: a dict of ports, which are pairs
            {'port_name': {'direction': ..., 'bounds': ...}, ... }
        :param iface_names: a tuple of interfaces names,
            that the ports shall be grouped into

        :return: a dict containing pairs { 'iface_name': [ports_names], ... }
        """
        iface_mappings = {}

        for iface in ifaces_names:
            iface_matches = list(filter(lambda port: port.name.startswith(iface), ports))
            if iface_matches:
                iface_mappings[iface] = iface_matches
            else:
                warning(f"found no matching ports for interface {iface}")

        return iface_mappings

    def __deduce_interface_mappings(self, ports):
        """Try to deduce names of interfaces by looking at ports prefixes"""
        # sort ports by name
        port_names = [port.name for port in ports]
        ports_sorted = sorted(port_names)
        ifaces_names = []

        (prefix, i, j) = self.__find_common_prefix(ports_sorted)
        while prefix:
            ifaces_names.append(prefix)
            ports_sorted = ports_sorted[:i] + ports_sorted[j + 1 :]
            (prefix, i, j) = self.__find_common_prefix(ports_sorted)

        return self.__create_interface_mappings(ifaces_names, ports)

    def __interface_mapping_from_yosys(self, hdl_file: str):
        """returns a dict
        {interface_name: [list of ports' names]}
        """
        json_file = hdl_file + ".json"
        subprocess.check_output(
            f'yosys -p "read_verilog {hdl_file}" ' f'-p "write_json {json_file}"', shell=True
        )

        modules = {}
        contents = []
        with open(json_file, "r") as jsf:
            contents = jsf.read()

        modules = json.loads(contents)["modules"]
        interfaces = dict()

        try:
            # TODO handle multiple modules
            module_name, module = modules.popitem()
            for name, port in module["netnames"].items():
                attrs = port["attributes"]
                if "interface" in attrs:
                    iface = attrs["interface"]
                    try:
                        interfaces[iface].append(name)
                    except KeyError:
                        interfaces[iface] = [name]
        except KeyError:
            pass

        return interfaces

    def get_interface_mappings(self, hdl_file: str, ports: Set[PortDefinition]):
        @functools.lru_cache
        def load_iface_yaml(filename):
            return safe_load(importlib.resources.read_text("topwrap.interfaces", filename))

        def iter_interfaces():
            for filename in importlib.resources.contents("topwrap.interfaces"):
                yield load_iface_yaml(filename)

        def match(ports, prefix):
            for yaml in iter_interfaces():
                score, signals = self.__interface_matching_score(yaml, ports, prefix)
                yield score, InterfaceMatch(signals, yaml["name"], prefix)

        iface_mappings = {}
        if self.use_yosys:
            iface_mappings = self.__interface_mapping_from_yosys(hdl_file)
        elif self.iface_deduce:
            iface_mappings = self.__deduce_interface_mappings(ports)
        elif self.ifaces_names:
            iface_mappings = self.__create_interface_mappings(self.ifaces_names, ports)

        ifaces = []
        for prefix, iface_ports in iface_mappings.items():
            matches = list(match(iface_ports, prefix))
            if matches:
                _, best_iface_match = max(matches, key=lambda t: t[0])  # select max by score
                if best_iface_match.signals:
                    ifaces.append(best_iface_match)

        return ifaces
