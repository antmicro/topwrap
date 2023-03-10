# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from logging import error
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson
from hdlConvertor import HdlConvertor
from .ip_desc import IPCoreDescription
from .hdl_parsers_utils import resolve_ops, group_ports_by_dir
from .hdl_parsers_interfaces import \
    deduce_interface_mappings, group_ports_to_ifaces, create_interface_mappings


def ipcore_desc_from_vhdl(vhdl_file, iface_names, iface_deduce):
    ''' Creates IPCoreDescription object using data gathered from VHDL
    '''
    # gather data from HDL
    c = HdlConvertor()
    d = c.parse([vhdl_file], Language.VHDL, [],
                hierarchyOnly=False, debug=True)

    try:
        data = ToJson().visit_HdlContext(d)
        mod = [x for x in data if x['__class__'] == 'HdlModuleDec'][0]
        name = mod['name']['val']

    except KeyError:
        raise
    except IndexError:
        error(f'No module found in {vhdl_file}!')  # TODO

    params = {}
    for item in mod['params']:
        param_val = resolve_ops(item['value'], params)
        if param_val is not None:
            params[item['name']['val']] = param_val

    ports = {
        item['name']['val']: {
            'direction': item['direction'],
            'bounds': item['type']
        }
        for item in mod['ports']
    }

    for port_name in ports.keys():
        if ports[port_name]['bounds'] == 'std_logic':
            ports[port_name]['bounds'] = (0, 0)
        else:
            resolved_ops = resolve_ops(ports[port_name]['bounds'], params)
            if resolved_ops is not None:
                ids = resolved_ops[1:-1].split(':') + ['0']
                ports[port_name]['bounds'] = (ids[0], ids[1])

    iface_mappings = {}
    if iface_deduce:
        iface_mappings = deduce_interface_mappings(ports)
    elif iface_names:
        iface_mappings = create_interface_mappings(ports, iface_names)

    ports_by_dir = group_ports_by_dir(ports)

    ifaces = group_ports_to_ifaces(iface_mappings, ports_by_dir)

    return IPCoreDescription(name, params, ports_by_dir, ifaces)


def parse_vhdl_sources(sources, iface_names, iface_deduce):
    for vhdl_file in sources:
        ip_desc = ipcore_desc_from_vhdl(vhdl_file, iface_names, iface_deduce)
        ip_desc.save('gen_' + ip_desc.name + '.yml')
