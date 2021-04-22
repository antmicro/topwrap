# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from .interface import get_interface_by_prefix


def check_interface_compliance(iface_def, signals):
    """Check if list of signal names matches the names in interface definition
    """
    required = iface_def.signals['required']
    optional = iface_def.signals['optional']

    for name in required:
        if name not in signals:
            return False
    for name in signals:
        if name not in required and name not in optional:
            return False
    return True


# This might be no longer needed
def match_interface(ports_matches):
    '''
    :param ports_matches: a list of pairs (port_name, signal_name), where
    signal_name is compatible with interface definition.
    The list must belong to a single instance of the interface
    :return: interface name if the list matches an interface correctly
    '''

    g_prefix = ports_matches[0][1].split('_')[0]
    g_instance = ports_matches[0][1].split('_')[1]
    iface = get_interface_by_prefix(g_prefix)

    for _, signal_name in ports_matches:
        prefix = signal_name.split('_')[0]
        instance = signal_name.split('_')[1]
        signal = signal_name.split('_')[2]

        # every port must belong to the same interface
        if prefix != iface.prefix:
            raise ValueError(f'signal prefix: {prefix} does not match'
                             f'the prefix of this interface: {iface.prefix}')
        # every port must belong to the same instance
        if instance != g_instance:
            raise ValueError(f'interface instance number: {instance} '
                             'does not match with other ports of '
                             f'this interface : {g_instance}')

        if signal not in iface.signals['required'] + iface.signals['optional']:
            raise ValueError(f'signal name: {signal_name} does not match any '
                             f'signal in interface definition: {iface.name}')

    return {'name': iface.name, 'ports': ports_matches}
