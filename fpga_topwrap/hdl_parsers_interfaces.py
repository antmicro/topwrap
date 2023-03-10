# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
from logging import warning


def _find_common_prefix(ports: list):
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


def create_interface_mappings(ports: dict, iface_names: tuple):
    ''' Try to create interface mappings by matching given interfaces names
    with ports names prefixes

    :param ports: a dict of ports, which are pairs
        {'port_name': {'direction': ..., 'bounds': ...}, ... }
    :param iface_names: a tuple of interfaces names,
        that the ports shall be grouped into

    :return: a dict containing pairs { 'iface_name': [ports_names], ... }
    '''
    iface_mappings = {}
    ports_names = ports.keys()

    for iface in iface_names:
        iface_matches = list(
            filter(lambda port: port.startswith(iface), ports_names))
        if iface_matches:
            iface_mappings[iface] = iface_matches
        else:
            warning(f'found no matching ports for interface {iface}')

    return iface_mappings


def deduce_interface_mappings(ports: dict):
    ''' Try to deduce names of interfaces by looking at ports prefixes
    '''
    # sort ports by name
    ports_sorted = sorted(ports.keys())
    ifaces_names = []

    (prefix, i, j) = _find_common_prefix(ports_sorted)
    while prefix:
        ifaces_names.append(prefix)
        ports_sorted = ports_sorted[:i] + ports_sorted[j+1:]
        (prefix, i, j) = _find_common_prefix(ports_sorted)

    return create_interface_mappings(ports, ifaces_names)


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
