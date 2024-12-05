# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from functools import cached_property
from logging import error
from pathlib import Path
from typing import Dict, Set

from hdlConvertor import HdlConvertor
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson
from simpleeval import SimpleEval
from typing_extensions import override

from .hdl_module import HDLModule, HDLParameter
from .hdl_parsers_utils import PortDefinition, PortDirection, resolve_ops


class VHDLModule(HDLModule):
    """This class contains data describing a single VHDL module.
    The VHDL file, from which the data is collected is parsed
    using HdlConvertor.
    """

    def __init__(self, vhdl_file: Path):
        super().__init__(vhdl_file)
        c = HdlConvertor()
        d = c.parse([str(vhdl_file)], Language.VHDL, [], hierarchyOnly=False, debug=True)

        try:
            data = ToJson().visit_HdlContext(d)
            self.__data = [x for x in data if x["__class__"] == "HdlModuleDec"][0]

        except KeyError:
            raise
        except IndexError:
            error(f"No module found in {vhdl_file}!")  # TODO

    @property
    @override
    def module_name(self) -> str:
        return self.__data["name"]["val"]

    @cached_property
    @override
    def parameters(self) -> Dict[str, HDLParameter]:
        params = {}
        for item in self.__data["params"]:
            param_val = resolve_ops(item["value"], params, SimpleEval())
            if param_val is not None:
                params[item["name"]["val"]] = param_val
        return params

    @cached_property
    @override
    def ports(self) -> Set[PortDefinition]:
        ports = set()

        for item in self.__data["ports"]:
            name = item["name"]["val"]
            direction = PortDirection(item["direction"].lower())
            type_or_bounds = item["type"]

            if type_or_bounds == "std_logic" or type_or_bounds == "std_ulogic":
                ubound, lbound = "0", "0"
            else:
                resolved_ops = resolve_ops(type_or_bounds, self.parameters, SimpleEval())
                if resolved_ops is not None:
                    ubound, lbound = resolved_ops[1:-1].split(":")
                else:
                    raise RuntimeError("Couldn't resolve widths of '{name}' port")

            ports.add(PortDefinition(name, ubound, lbound, direction))

        return ports
