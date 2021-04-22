# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson
from hdlConvertor import HdlConvertor
from .ip_desc import IPCoreDescription
from .verilog_parser import _resolve_ops
# TODO either merge verilog and vhdl parsers or make _resolve_ops external


def ipcore_desc_from_vhdl(vhdl_file):
    ''' Creates IPCoreDescription object using data gathered from Verilog
    '''
    # gather data from HDL
    c = HdlConvertor()
    d = c.parse([vhdl_file], Language.VHDL, [],
                hierarchyOnly=False, debug=True)

    try:
        data = ToJson().visit_HdlContext(d)
        #mod = filter(lambda x: x['__class__'] == 'HdlModuleDec', data)[0]
        mod = [x for x in data if x['__class__'] == 'HdlModuleDec'][0]
        name = mod['name']['val']

        params = {item['name']['val']:
                  # TODO resolve complex cases as in verilog_parser.py
                  item['value']
                  for item in mod['params']}

        ports = {item['name']['val']: {'direction': item['direction'],
                                       'bounds': item['type']}
                 for item in mod['ports']}

    except KeyError:
        raise
    except IndexError:
        error(f'No module found in {vhdl_file}!')  # TODO

    # TODO resolve complex expressions in parameters

    # TODO filter out None-valued parameters

    for port_name in ports.keys():
        if ports[port_name]['bounds'] == 'std_logic':
            ports[port_name]['bounds'] = (0, 0)
        else:
            ids = _resolve_ops(ports[port_name]['bounds']).split(':') + ['0']
            ports[port_name]['bounds'] = (ids[0], ids[1])

    for port_name in ports.keys():
        print(port_name, ports[port_name])

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

    # TODO get interface mappings and group `ports_new` accordingly
    ifaces = {}
    print(name)
    print(params)
    #print(ports_new)

    return IPCoreDescription(name, params, ports_new, ifaces)
