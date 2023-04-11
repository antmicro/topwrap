# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from logging import error
import subprocess
import json
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson
from hdlConvertor import HdlConvertor
from .ip_desc import IPCoreDescription
from .hdl_parsers_utils import resolve_ops, group_ports_by_dir
from .hdl_parsers_interfaces import InterfaceGrouper, group_ports_to_ifaces


def ipcore_desc_from_verilog(verilog_file, ifaces_names, iface_deduce):
    ''' Creates IPCoreDescription object using data gathered from Verilog
    '''

    # gather data from HDL
    c = HdlConvertor()
    d = c.parse([verilog_file], Language.VERILOG, [],
                hierarchyOnly=False, debug=True)

    try:
        data = ToJson().visit_HdlContext(d)[0]
        name = data['module_name']
        dec = data['dec']

    except KeyError:
        raise
    except IndexError:
        error(f'No module found in {verilog_file}!')  # TODO

    params = {}
    for item in dec['params']:
        param_val = resolve_ops(item['value'], params)
        if param_val is not None:
            params[item['name']['val']] = param_val

    ports = {
        item['name']['val']: {
            'direction': item['direction'],
            'bounds': item['type']
        }
        for item in dec['ports']
    }

    for port_name in ports.keys():
        # 1-bit wide ports:
        # '(in|out)put port_name' or '(in|out)put wire port_name'
        if ports[port_name]['bounds'] == 'wire' or \
          ports[port_name]['bounds']['__class__'] == 'HdlTypeAuto':
            ports[port_name]['bounds'] = ('0', '0')
        else:
            resolved_ops = resolve_ops(ports[port_name]['bounds'], params)
            if resolved_ops is not None:
                ids = resolved_ops[1:-1].split(':') + ['0']
                ports[port_name]['bounds'] = (ids[0], ids[1])

    iface_grouper = InterfaceGrouper(ports, verilog_file)
    iface_mappings = iface_grouper.get_interface_mappings(True, iface_deduce, ifaces_names)

    ports_by_dir = group_ports_by_dir(ports)

    ifaces = group_ports_to_ifaces(iface_mappings, ports_by_dir)

    return IPCoreDescription(name, params, ports_by_dir, ifaces)


def parse_verilog_sources(sources, iface_names, iface_deduce):
    for verilog_file in sources:
        ip_desc = ipcore_desc_from_verilog(
            verilog_file, iface_names, iface_deduce)
        ip_desc.save('gen_' + ip_desc.name + '.yml')
