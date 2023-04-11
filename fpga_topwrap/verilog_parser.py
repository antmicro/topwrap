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


class VerilogModule:
    """ This class contains data describing a single Verilog module.
    The verilog file, from which the data is collected is parsed
    using HdlConvertor.
    """

    def __init__(self, verilog_file: str):
        self.filename = verilog_file
        c = HdlConvertor()
        d = c.parse([self.filename], Language.VERILOG, [],
                    hierarchyOnly=False, debug=True)

        try:
            self.__data = ToJson().visit_HdlContext(d)[0]

        except KeyError:
            raise
        except IndexError:
            error(f'No module found in {self.filename}!')

    def get_module_name(self):
        return self.__data['module_name']

    def get_parameters(self):
        params = {}
        for item in self.__data['dec']['params']:
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
            for item in self.__data['dec']['ports']
        }

        for port_name in ports.keys():
            # 1-bit wide ports:
            # '(in|out)put port_name' or '(in|out)put wire port_name'
            if ports[port_name]['bounds'] == 'wire' or \
                    ports[port_name]['bounds']['__class__'] == 'HdlTypeAuto':
                ports[port_name]['bounds'] = ('0', '0')
            else:
                resolved_ops = resolve_ops(
                    ports[port_name]['bounds'], self.get_parameters())
                if resolved_ops is not None:
                    ids = resolved_ops[1:-1].split(':') + ['0']
                    ports[port_name]['bounds'] = (ids[0], ids[1])
        return ports


def ipcore_desc_from_verilog_module(
        verilog_mod: VerilogModule,
        iface_grouper: InterfaceGrouper) -> IPCoreDescription:

    mod_name = verilog_mod.get_module_name()
    parameters = verilog_mod.get_parameters()
    ports = verilog_mod.get_ports()

    ports_by_direction = group_ports_by_dir(ports)

    iface_mappings = iface_grouper.get_interface_mappings(
        verilog_mod.filename, ports)
    ifaces = group_ports_to_ifaces(iface_mappings, ports_by_direction)

    return IPCoreDescription(mod_name, parameters, ports_by_direction, ifaces)
