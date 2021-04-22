# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from logging import error, warning
import subprocess
import json
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson
from hdlConvertor import HdlConvertor
from .ip_desc import IPCoreDescription


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


def _resolve_ops(ops):
    ''' ops is a complex expression gathered from HdlConvertor data ('HdlOp')
    it contains nested dicts of operations
    This function uses them to get widths of ports
    as numbers or math expressions
    '''

    if isinstance(ops, str):
        return ops
    try:
        cls = ops['__class__']
    except TypeError:
        return str(ops)

    if cls == 'HdlValueInt':
        return str(ops['val'])

    elif cls == 'HdlOp':
        fn = ops['fn']
        if fn == 'PARAMETRIZATION':
            return _resolve_ops(ops['ops'][1])
        elif fn == 'DOWNTO':
            return (str(_resolve_ops(ops['ops'][0])) + ':'
                    + str(_resolve_ops(ops['ops'][1])))
        elif fn == 'SUB':
            return (str(_resolve_ops(ops['ops'][0])) + '-'
                    + str(_resolve_ops(ops['ops'][1])))
        elif fn == 'MUL':
            return (str(_resolve_ops(ops['ops'][0])) + '*'
                    + str(_resolve_ops(ops['ops'][1])))
        elif fn == 'DIV':
            return (str(_resolve_ops(ops['ops'][0])) + '/'
                    + str(_resolve_ops(ops['ops'][1])))
        elif fn == 'INDEX':
            # this happens in 'std_logic_vector({upper_id DOWNTO lower_id})
            # drop `std_logic_vector` and process the insides of parentheses
            return _resolve_ops(ops['ops'][1])
        else:
            warning(f'Unhandled HdlOp function: {fn}')
    else:
        warning(f'Unhandled HdlOp class: {cls}')


def ipcore_desc_from_verilog(verilog_file):
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

        params = {item['name']['val']:
                  # value has either a 'val' (explicit value)
                  # or 'ops' which is a complex expression
                  item['value'].get('val', item['value'])
                  for item in dec['params']}

        ports = {item['name']['val']: {'direction': item['direction'],
                                       'bounds': item['type']}
                 for item in dec['ports']}

    except IndexError:
        error(f'No module found in {verilog_file}!')  # TODO

    # resolve complex expressions
    for param_name in params.keys():
        if not isinstance(params[param_name], str):
            params[param_name] = _resolve_ops(params[param_name])
        if not params[param_name]:
            warning(f"default value of parameter {param_name} "
                    "couldn't be parsed")

    # filter out None-valued parameters
    params = {n: v for n, v in params.items() if v}

    for port_name in ports.keys():
        if ports[port_name]['bounds']['__class__'] == 'HdlTypeAuto':
            ports[port_name]['bounds'] = (0, 0)
        else:
            # port indices represented as:
            #   N_BITS-1:0
            #   N_BITS-1 defaults to N_BITS-1:0
            # convert these to
            #   N_BITS-1, 0, N_BITS-1, 0
            ids = _resolve_ops(ports[port_name]['bounds']).split(':') + ['0']
            ports[port_name]['bounds'] = (ids[0], ids[1])

    # restructure ports to group them by direction
    ports_new = {'in': [], 'out': [], 'inout': []}
    for port_name, port in ports.items():
        d = port['direction']
        if d == 'IN':
            ports_new['in'].append({'name': port_name,
                                    'bounds': port['bounds']})
        elif d == 'OUT':
            ports_new['out'].append({'name': port_name,
                                    'bounds': port['bounds']})
        else:
            ports_new['inout'].append({'name': port_name,
                                      'bounds': port['bounds']})

    iface_mappings = get_interface_mapping_from_yosys(verilog_file)
    ifaces = dict()
    for iface_name in iface_mappings.keys():
        ifaces[iface_name] = dict()
        ifaces[iface_name]['in'] = []
        ifaces[iface_name]['out'] = []
        ifaces[iface_name]['inout'] = []

    # all the ports are stored in `ports_new` dict
    # those which belong to interfaces shall be moved to a new dict
    for iface_name, ports_list in iface_mappings.items():
        for port_name in ports_list:
            in_matches = list(filter(lambda port: port['name'] == port_name,
                                     ports_new['in']))
            out_matches = list(filter(lambda port: port['name'] == port_name,
                                      ports_new['out']))
            inout_matches = list(filter(lambda port: port['name'] == port_name,
                                        ports_new['inout']))

            if len(in_matches) > 0:
                ifaces[iface_name]['in'].append(in_matches[0])
                ports_new['in'].remove(in_matches[0])
            elif len(out_matches) > 0:
                ifaces[iface_name]['out'].append(out_matches[0])
                ports_new['out'].remove(out_matches[0])
            elif len(inout_matches) > 0:
                ifaces[iface_name]['inout'].append(inout_matches[0])
                ports_new['inout'].remove(inout_matches[0])

    return IPCoreDescription(name, params, ports_new, ifaces)
