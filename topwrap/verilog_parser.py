# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from functools import cached_property
from logging import error
from typing import Dict, List, Set

from hdlConvertor import HdlConvertor
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.json import ToJson
from simpleeval import SimpleEval
from typing_extensions import override

from .hdl_module import HDLModule, HDLParameter
from .hdl_parsers_utils import PortDefinition, PortDirection, resolve_ops


class VerilogModule(HDLModule):
    """This class contains data describing a single Verilog module.
    The verilog file, from which the data is collected is parsed
    using HdlConvertor.
    """

    def __init__(self, verilog_file: str, verilog_module: dict):
        super().__init__(verilog_file)
        self._data = verilog_module

    @property
    @override
    def module_name(self) -> str:
        return self._data["module_name"]

    @cached_property
    @override
    def parameters(self) -> Dict[str, HDLParameter]:
        params = {}
        for item in self._data["dec"]["params"]:
            param_val = resolve_ops(item["value"], params, SimpleEval())
            if param_val is not None:
                params[item["name"]["val"]] = param_val
        return params

    @cached_property
    @override
    def ports(self) -> Set[PortDefinition]:
        ports = set()

        for item in self._data["dec"]["ports"]:
            name = item["name"]["val"]
            direction = PortDirection(item["direction"].lower())
            type_or_bounds = item["type"]
            # 1-bit wide ports:
            # '(in|out)put port_name' or '(in|out)put wire port_name'
            if type_or_bounds == "wire" or type_or_bounds["__class__"] == "HdlTypeAuto":
                ubound, lbound = "0", "0"
            else:
                resolved_ops = resolve_ops(type_or_bounds, self.parameters, SimpleEval())
                if resolved_ops is not None:
                    ubound, lbound = resolved_ops[1:-1].split(":")
                else:
                    raise RuntimeError("Couldn't resolve widths of '{name}' port")

            ports.add(PortDefinition(name, ubound, lbound, direction))

        return ports

    @cached_property
    def components(self) -> Set[str]:
        """Returns a set of other module names that get instantiated in this module"""

        def _recurse_components(objs) -> Set[str]:
            components: Set[str] = set()

            if (
                isinstance(objs, dict)
                and "__class__" in objs
                and objs["__class__"] == "HdlCompInst"
            ):
                components.add(objs["module_name"])
            elif isinstance(objs, dict):
                for obj in objs:
                    components = components.union(_recurse_components(objs[obj]))
            elif isinstance(objs, list):
                for obj in objs:
                    components = components.union(_recurse_components(obj))

            return components

        components = _recurse_components(self._data["objs"])
        components.discard(self.module_name)
        return components


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
