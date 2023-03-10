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
from .hdl_parsers_interfaces import \
    deduce_interface_mappings, group_ports_to_ifaces, create_interface_mappings


def verilog_to_json(verilog_filename, json_filename):
    """Given filenames of Verilog source and JSON target,
    use 'write_json' function of yosys
    """
    subprocess.check_output(f'yosys -p "read_verilog {verilog_filename}" '
                            f'-p "write_json {json_filename}"', shell=True)


def get_interface_mapping_from_yosys(verilog_file):
    """ returns a dict
        {interface_name: [list of ports' names]}
    """
    json_file = verilog_file + '.json'
    verilog_to_json(verilog_file, json_file)

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


def ipcore_desc_from_verilog(verilog_file, iface_names, iface_deduce):
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

    iface_mappings = {}
    if not iface_deduce and not iface_names:
        iface_mappings = get_interface_mapping_from_yosys(verilog_file)
    elif iface_deduce:
        iface_mappings = deduce_interface_mappings(ports)
    elif iface_names:
        iface_mappings = create_interface_mappings(ports, iface_names)

    ports_by_dir = group_ports_by_dir(ports)

    ifaces = group_ports_to_ifaces(iface_mappings, ports_by_dir)

    return IPCoreDescription(name, params, ports_by_dir, ifaces)


def parse_verilog_sources(sources, iface_names, iface_deduce):
    for verilog_file in sources:
        ip_desc = ipcore_desc_from_verilog(
            verilog_file, iface_names, iface_deduce)
        ip_desc.save('gen_' + ip_desc.name + '.yml')
