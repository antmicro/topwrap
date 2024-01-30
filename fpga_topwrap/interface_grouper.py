# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import json
import subprocess
from logging import warning


class InterfaceGrouper:
    """This class provides a possibility to group ports of a specific HDL file
    into different interfaces (e.g AXI, AXILite...).
    """

    def __init__(self, use_yosys: bool, iface_deduce: bool, ifaces_names: tuple):
        """Set config variables which determine, how to perform grouping."""
        self.use_yosys = use_yosys
        self.iface_deduce = iface_deduce
        self.ifaces_names = ifaces_names

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
        def _heuristic(pref_len: int, count: int):
            return pref_len * pref_len * count

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
                heur = _heuristic(dp_mins[i][j], j - i + 1)
                if heur > best_heur and heur > min_heur_value:
                    best_i, best_j = i, j
                    best_heur, best_prefix = heur, ports[i][: dp_mins[i][j]]
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
        ports_names = ports.keys()

        for iface in ifaces_names:
            iface_matches = list(filter(lambda port: port.startswith(iface), ports_names))
            if iface_matches:
                iface_mappings[iface] = iface_matches
            else:
                warning(f"found no matching ports for interface {iface}")

        return iface_mappings

    def __deduce_interface_mappings(self, ports):
        """Try to deduce names of interfaces by looking at ports prefixes"""
        # sort ports by name
        ports_sorted = sorted(ports.keys())
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

    def get_interface_mappings(self, hdl_file: str, ports: dict):
        iface_mappings = {}
        if self.use_yosys:
            iface_mappings = self.__interface_mapping_from_yosys(hdl_file)
        elif self.iface_deduce:
            iface_mappings = self.__deduce_interface_mappings(ports)
        elif self.ifaces_names:
            iface_mappings = self.__create_interface_mappings(self.ifaces_names, ports)
        return iface_mappings
