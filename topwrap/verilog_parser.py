# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from logging import error
from typing import Dict, List, Set, Union

from hdlConvertor import HdlConvertor
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson

from .hdl_module import HDLModule
from .hdl_parsers_utils import PortDefinition, PortDirection, resolve_ops


class VerilogModule(HDLModule):
    """This class contains data describing a single Verilog module.
    The verilog file, from which the data is collected is parsed
    using HdlConvertor.
    """

    def __init__(self, verilog_file: str, verilog_module: dict):
        super().__init__(verilog_file)
        self.__data = verilog_module

    def get_module_name(self) -> str:
        return self.__data["module_name"]

    def get_parameters(self) -> Dict[str, Union[int, str, Dict[str, int]]]:
        params = {}
        for item in self.__data["dec"]["params"]:
            param_val = resolve_ops(item["value"], params)
            if param_val is not None:
                params[item["name"]["val"]] = param_val
        return params

    def get_ports(self) -> Set[PortDefinition]:
        ports = set()

        for item in self.__data["dec"]["ports"]:
            name = item["name"]["val"]
            direction = PortDirection(item["direction"].lower())
            type_or_bounds = item["type"]
            # 1-bit wide ports:
            # '(in|out)put port_name' or '(in|out)put wire port_name'
            if type_or_bounds == "wire" or type_or_bounds["__class__"] == "HdlTypeAuto":
                ubound, lbound = "0", "0"
            else:
                resolved_ops = resolve_ops(type_or_bounds, self.get_parameters())
                if resolved_ops is not None:
                    ubound, lbound = resolved_ops[1:-1].split(":")
                else:
                    raise RuntimeError("Couldn't resolve widths of '{name}' port")

            ports.add(PortDefinition(name, ubound, lbound, direction))

        return ports


class VerilogModuleGenerator:
    def __init__(self):
        self.conv = HdlConvertor()

    def get_modules(self, file: str) -> List[VerilogModule]:
        try:
            hdl_context = self.conv.parse(
                [file], Language.VERILOG, [], hierarchyOnly=False, debug=True
            )
        except IndexError:
            error(f"No module found in {file}!")

        modules = ToJson().visit_HdlContext(hdl_context)
        return [VerilogModule(file, module) for module in modules]
