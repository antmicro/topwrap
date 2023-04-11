# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from logging import error
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson
from hdlConvertor import HdlConvertor
from .ip_desc import IPCoreDescription
from .hdl_parsers_utils import \
    resolve_ops, group_ports_by_dir, group_ports_to_ifaces
from .interface_grouper import InterfaceGrouper


class VHDLModule:
    """ This class contains data describing a single VHDL module.
    The VHDL file, from which the data is collected is parsed
    using HdlConvertor.
    """

    def __init__(self, vhdl_file: str):
        self.filename = vhdl_file
        c = HdlConvertor()
        d = c.parse([vhdl_file], Language.VHDL, [],
                    hierarchyOnly=False, debug=True)

        try:
            data = ToJson().visit_HdlContext(d)
            self.__data = [x for x in data if x['__class__']
                           == 'HdlModuleDec'][0]

        except KeyError:
            raise
        except IndexError:
            error(f'No module found in {vhdl_file}!')  # TODO

    def get_module_name(self):
        return self.__data['name']['val']

    def get_parameters(self):
        params = {}
        for item in self.__data['params']:
            param_val = resolve_ops(item['value'], params)
            if param_val is not None:
                params[item['name']['val']] = param_val
        return params

    def get_ports(self):
        ports = {
            item['name']['val']: {
                'direction': item['direction'],
                'bounds': item['type']
            }
            for item in self.__data['ports']
        }

        for port_name in ports.keys():
            if ports[port_name]['bounds'] == 'std_logic' or \
                    ports[port_name]['bounds'] == 'std_ulogic':
                ports[port_name]['bounds'] = (0, 0)
            else:
                resolved_ops = resolve_ops(
                    ports[port_name]['bounds'], self.get_parameters())
                if resolved_ops is not None:
                    ids = resolved_ops[1:-1].split(':') + ['0']
                    ports[port_name]['bounds'] = (ids[0], ids[1])
        return ports


def ipcore_desc_from_vhdl_module(
        vhdl_mod: VHDLModule,
        iface_grouper: InterfaceGrouper) -> IPCoreDescription:

    mod_name = vhdl_mod.get_module_name()
    parameters = vhdl_mod.get_parameters()
    ports = vhdl_mod.get_ports()

    ports_by_direction = group_ports_by_dir(ports)

    iface_mappings = iface_grouper.get_interface_mappings(
        vhdl_mod.filename, ports)
    ifaces = group_ports_to_ifaces(iface_mappings, ports_by_direction)

    return IPCoreDescription(mod_name, parameters, ports_by_direction, ifaces)
