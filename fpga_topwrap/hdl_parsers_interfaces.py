# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
from logging import warning
import json
import subprocess


class InterfaceGrouper:
    """ This class provides a couple of functions which goal is to group
    ports into different interfaces (e.g AXI, AXILite...)
    """

    def __init__(self, ports: dict, hdl_file: str):
        self.ports = ports
        self.hdl_file = hdl_file


    def __find_common_prefix(self, ports: list):
        ''' Find a prefix that is the most common among ports names.

        :param ports: sorted list of ports names

        :return: (prefix, i, j) i - first, j - last index where the prefix occurs
        '''
        # longest common prefix function
        def _lcp(str1: str, str2: str):
            for i in range(min(len(str1), len(str2))):
                if str1[i] != str2[i]:
                    break
            return str1[:i]

        # simple heuristic that is used to prefer less names with longer prefixes
        # than more names with shorter prefixes
        def _heuristic(pref_len: int, count: int):
            return pref_len * pref_len * count

        lcp_prev = [1] + [0] * (len(ports) - 1)
        for i in range(1, len(ports)):
            lcp_prev[i] = len(_lcp(ports[i], ports[i-1]))

        # dp_mins[i][j] - minimal value of lcp_prev[i:j+1]
        dp_mins = [[0 for _ in range(len(lcp_prev))] for _ in range(len(lcp_prev))]
        for i in range(len(lcp_prev)):
            for j in range(i, len(lcp_prev)):
                if i == j:
                    dp_mins[i][j] = lcp_prev[i]
                else:
                    dp_mins[i][j] = min(lcp_prev[j], dp_mins[i][j-1])

        min_num_prefixes = 3  # don't consider prefixes that occur <=3 times
        min_heur_value = 10  # don't consider very short prefixes
        best_heur, best_prefix, best_i, best_j = 0, "", -1, -1
        # find prefix for which the heuristic value is the highest
        for i in range(len(lcp_prev)):
            for j in range(i+min_num_prefixes, len(lcp_prev)):
                heur = _heuristic(dp_mins[i][j], j-i+1)
                if heur > best_heur and heur > min_heur_value:
                    best_i, best_j = i, j
                    best_heur, best_prefix = heur, ports[i][:dp_mins[i][j]]
        return (best_prefix.rstrip("_"), best_i - 1, best_j)
    

    def __create_interface_mappings(self, ifaces_names: tuple):
        ''' Try to create interface mappings by matching given interfaces names
        with ports names prefixes

        :param ports: a dict of ports, which are pairs
            {'port_name': {'direction': ..., 'bounds': ...}, ... }
        :param iface_names: a tuple of interfaces names,
            that the ports shall be grouped into

        :return: a dict containing pairs { 'iface_name': [ports_names], ... }
        '''
        iface_mappings = {}
        ports_names = self.ports.keys()

        for iface in ifaces_names:
            iface_matches = list(
                filter(lambda port: port.startswith(iface), ports_names))
            if iface_matches:
                iface_mappings[iface] = iface_matches
            else:
                warning(f'found no matching ports for interface {iface}')

        return iface_mappings


    def __deduce_interface_mappings(self):
        ''' Try to deduce names of interfaces by looking at ports prefixes
        '''
        # sort ports by name
        ports_sorted = sorted(self.ports.keys())
        ifaces_names = []

        (prefix, i, j) = self.__find_common_prefix(ports_sorted)
        while prefix:
            ifaces_names.append(prefix)
            ports_sorted = ports_sorted[:i] + ports_sorted[j+1:]
            (prefix, i, j) = self.__find_common_prefix(ports_sorted)

        return self.__create_interface_mappings(ifaces_names)
    

    def __interface_mapping_from_yosys(self):
        """ returns a dict
            {interface_name: [list of ports' names]}
        """
        json_file = self.hdl_file + '.json'
        subprocess.check_output(f'yosys -p "read_verilog {self.hdl_file}" '
                            f'-p "write_json {json_file}"', shell=True)

        modules = {}
        contents = []
        with open(json_file, 'r') as jsf:
            contents = jsf.read()

        modules = json.loads(contents)['modules']
        interfaces = dict()

        try:
            # TODO handle multiple modules
            module_name, module = modules.popitem()
            for name, port in module['netnames'].items():
                attrs = port['attributes']
                if 'interface' in attrs:
                    iface = attrs['interface']
                    try:
                        interfaces[iface].append(name)
                    except KeyError:
                        interfaces[iface] = [name]
        except KeyError:
            pass

        return interfaces


    def get_interface_mappings(self, use_yosys: bool, iface_deduce: bool, ifaces_names: tuple):
        iface_mappings = {}
        if use_yosys:
            iface_mappings = self.__interface_mapping_from_yosys()
        elif iface_deduce:
            iface_mappings = self.__deduce_interface_mappings()
        elif ifaces_names:
            iface_mappings = self.__create_interface_mappings(ifaces_names)
        return iface_mappings


def group_ports_to_ifaces(iface_mappings: dict, ports: dict):
    ''' Group `ports` into interfaces, based on `iface_mappings

    :param iface_mappings: a dict containing pairs
        { 'iface_name': [ports_names], ... }
    :param ports: a dict of ports, grouped by direction -
        {'in': [], 'out': [], 'inout': []}

    :return: a dict containing ports names, grouped into interfaces
    '''
    ifaces = {}
    for iface_name in iface_mappings.keys():
        ifaces[iface_name] = dict()
        ifaces[iface_name]['in'] = []
        ifaces[iface_name]['out'] = []
        ifaces[iface_name]['inout'] = []

    # all the ports are stored in `ports` dict
    # those which belong to interfaces shall be moved to a new dict
    for iface_name, ports_list in iface_mappings.items():
        for port_name in ports_list:
            in_matches = list(filter(lambda port: port['name'] == port_name,
                                     ports['in']))
            out_matches = list(filter(lambda port: port['name'] == port_name,
                                      ports['out']))
            inout_matches = list(filter(lambda port: port['name'] == port_name,
                                        ports['inout']))

            if len(in_matches) > 0:
                ifaces[iface_name]['in'].append(in_matches[0])
                ports['in'].remove(in_matches[0])
            elif len(out_matches) > 0:
                ifaces[iface_name]['out'].append(out_matches[0])
                ports['out'].remove(out_matches[0])
            elif len(inout_matches) > 0:
                ifaces[iface_name]['inout'].append(inout_matches[0])
                ports['inout'].remove(inout_matches[0])

    return ifaces
