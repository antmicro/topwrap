# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from logging import warning
from typing import Iterable

import numexpr as ex


class PortDirection(Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"


@dataclass(frozen=True)
class PortDefinition:
    name: str
    upper_bound: str
    lower_bound: str
    direction: PortDirection


def _eval_param(val, params: dict):
    """Function used to calculate parameter value.
    It is used for evaluating CONCAT and REPL_CONCAT in resolve_ops()"""
    if isinstance(val, int):
        return val
    if isinstance(val, dict) and val.keys() == {"value", "width"}:
        return val
    if isinstance(val, str):
        return _eval_param(params[val], params)

    elif val["__class__"] == "HdlValueInt":
        value = int(val["val"], val["base"])
        if "bits" not in val.keys():
            return value
        else:
            return {"value": hex(value), "width": val["bits"]}

    elif val["__class__"] == "HdlOp":
        if val["fn"] == "CONCAT":
            bit_vector_l = _eval_param(val["ops"][0], params)
            bit_vector_r = _eval_param(val["ops"][1], params)
            bin_l = bin(int(bit_vector_l["value"], 16))[2:].zfill(bit_vector_l["width"])
            bin_r = bin(int(bit_vector_r["value"], 16))[2:].zfill(bit_vector_r["width"])
            return {
                "value": hex(int(bin_l + bin_r, 2)),
                "width": bit_vector_l["width"] + bit_vector_r["width"],
            }

        elif val["fn"] == "REPL_CONCAT":
            repeat = _eval_param(val["ops"][0], params)
            bit_vector = _eval_param(val["ops"][1], params)
            bin_val = bin(int(bit_vector["value"], 16))[2:].zfill(bit_vector["width"])
            return {"value": hex(int(repeat * bin_val, 2)), "width": repeat * bit_vector["width"]}

        else:
            return int(ex.evaluate(resolve_ops(val, params)).take(0))


def resolve_ops(val, params: dict):
    """Get 'val' representation, that will be used in ip core yaml

    :param val: expression gathered from HdlConvertor data.
    It contains nested dicts of operations.

    Return value:

    * if 'val' is a number or another parameter name - return 'val'
    * if 'val' is a fixed-width parameter (e.g. "parameter PARAM = 2'b10") -
    return a dictionary { 'value': ..., 'width': ... }
    * if 'val' is 'HdlOp' - return a string representing 'val' as
    a math expression (i.e. don't evaluate the default parameter value)
    * if 'val' is 'HdlOp' and is an expression of type (REPL_)CONCAT evaluate
    its default value and return as a { 'value': ..., 'width': ... } dict
    """

    if isinstance(val, int) or isinstance(val, str):
        return val

    elif val["__class__"] == "HdlValueInt":
        value = int(val["val"], val["base"])
        if "bits" not in val.keys():
            return value
        else:
            return {"value": hex(value), "width": val["bits"]}

    elif val["__class__"] == "HdlOp":
        bin_ops = {
            "SUB": "-",
            "ADD": "+",
            "DIV": "/",
            "MUL": "*",
            "MOD": "%",
            "POW": "**",
            "EQ": "==",
            "NE": "!=",
            "LT": "<",
            "LE": "<=",
            "GT": ">",
            "GE": ">=",
            "DOWNTO": ":",
        }

        if val["fn"] in bin_ops.keys():
            op = bin_ops[val["fn"]]
            left = resolve_ops(val["ops"][0], params)
            right = resolve_ops(val["ops"][1], params)
            if left is None or right is None:
                return None
            else:
                return "(" + str(left) + op + str(right) + ")"

        elif val["fn"] == "TERNARY":
            cond = resolve_ops(val["ops"][0], params)
            if_true = resolve_ops(val["ops"][1], params)
            if_false = resolve_ops(val["ops"][2], params)
            if cond is None or if_true is None or if_false is None:
                return None
            else:
                return "where(" + str(cond) + ", " + str(if_true) + ", " + str(if_false) + ")"

        elif val["fn"] == "CONCAT" or val["fn"] == "REPL_CONCAT":
            # TODO - try to find a better way to get parameters default values
            # than copying params and evaluating them before each (REPL_)CONCAT
            params_cp = params.copy()
            for name in params_cp.keys():
                if isinstance(params_cp[name], str):
                    params_cp[name] = int(ex.evaluate(params_cp[name], params_cp).take(0))

            return _eval_param(val, params_cp)

        elif val["fn"] == "PARAMETRIZATION":
            if (
                val["ops"][0] == "reg"
                and val["ops"][1]["__class__"] == "str"
                and val["ops"][1]["val"] is None
            ):
                # corner case - this happens in Verilog's output/input reg
                return "(0:0)"
            return resolve_ops(val["ops"][1], params)

        elif val["fn"] == "INDEX":
            # this happens in VHDL's 'std_logic_vector({up_id DOWNTO low_id})
            # drop `std_logic_vector` and process the insides of parentheses
            return resolve_ops(val["ops"][1], params)
        elif val["fn"] == "CALL":
            return f"{resolve_ops(val['ops'][0], params)}({','.join(resolve_ops(arg, params) for arg in val['ops'][1:])})"
        else:
            warning(f'resolve_ops: unhandled HdlOp function: {val["fn"]}')
