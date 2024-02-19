# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from logging import error
from typing import Dict, Set, Union

from hdlConvertor import HdlConvertor
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson

from .hdl_module import HDLModule
from .hdl_parsers_utils import PortDefinition, PortDirection, resolve_ops


class VHDLModule(HDLModule):
    """This class contains data describing a single VHDL module.
    The VHDL file, from which the data is collected is parsed
    using HdlConvertor.
    """

    def __init__(self, vhdl_file: str):
        super().__init__(vhdl_file)
        c = HdlConvertor()
        d = c.parse([vhdl_file], Language.VHDL, [], hierarchyOnly=False, debug=True)

        try:
            data = ToJson().visit_HdlContext(d)
            self.__data = [x for x in data if x["__class__"] == "HdlModuleDec"][0]

        except KeyError:
            raise
        except IndexError:
            error(f"No module found in {vhdl_file}!")  # TODO

    def get_module_name(self) -> str:
        return self.__data["name"]["val"]

    def get_parameters(self) -> Dict[str, Union[int, str, Dict[str, int]]]:
        params = {}
        for item in self.__data["params"]:
            param_val = resolve_ops(item["value"], params)
            if param_val is not None:
                params[item["name"]["val"]] = param_val
        return params

    def get_ports(self) -> Set[PortDefinition]:
        ports = set()

        for item in self.__data["ports"]:
            name = item["name"]["val"]
            direction = PortDirection(item["direction"].lower())
            type_or_bounds = item["type"]

            if type_or_bounds == "std_logic" or type_or_bounds == "std_ulogic":
                ubound, lbound = "0", "0"
            else:
                resolved_ops = resolve_ops(type_or_bounds, self.get_parameters())
                if resolved_ops is not None:
                    ubound, lbound = resolved_ops[1:-1].split(":")
                else:
                    raise RuntimeError("Couldn't resolve widths of '{name}' port")

            ports.add(PortDefinition(name, ubound, lbound, direction))

        return ports
