# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import re
from collections import deque
from dataclasses import dataclass
from enum import Enum
from logging import warning
from typing import Any, Dict, List, Union

from simpleeval import DEFAULT_FUNCTIONS, NameNotDefined, SimpleEval, simple_eval

from topwrap.amaranth_helpers import DIR_IN, DIR_INOUT, DIR_OUT

HDLParameter = Union[int, str, Dict[str, int]]


class PortDirection(Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"

    def to_amaranth(self):
        return DIR_IN if self == self.IN else DIR_OUT if self == self.OUT else DIR_INOUT


@dataclass(frozen=True)
class PortDefinition:
    name: str
    upper_bound: str
    lower_bound: str
    direction: PortDirection


@dataclass
class ParameterToEval:
    name: str
    value: Union[str, int, Dict[str, Any]]
    ip_core: str  # Name of ip core where this parameter exists


@dataclass(frozen=True)
class EvaluatedParamsReturnType:
    evaluated_dict: Dict[str, HDLParameter]
    not_evaluated: List[ParameterToEval]


def parse_value_width_parameter(param: str) -> Dict[str, int]:
    """`param` is a string representing a bit vector in Verilog format
    (e.g. "16'h5A5A") which is parsed to a value/width parameter
    """
    quote_pos = param.find("'")
    width = param[:quote_pos]
    radix = param[quote_pos + 1]
    value = param[quote_pos + 2 :]
    radix_to_base = {"h": 16, "d": 10, "o": 8, "b": 2}

    return {"value": int(value, radix_to_base[radix]), "width": int(width)}


def evaluate_parameter_list(parameters: List[ParameterToEval]) -> EvaluatedParamsReturnType:
    """
    Evaluates a list of parameters by resolving their values in dependency order.

    Parameters are processed iteratively: resolved values are stored, while unresolved ones
    are retried until all evaluable parameters are resolved or deemed invalid.

    Args:
        parameters (List[ParameterToEval]): List of parameters to evaluate.

    Returns:
        EvaluatedParamsReturnType: A result containing successfully evaluated parameters
                                   and a list of invalid parameters that could not be resolved.
    """
    worklist = deque()
    evaluated = {}
    invalid_parameters = []

    for parameter in parameters:
        worklist.append(parameter)

    fail_count = 0
    while worklist and fail_count < len(worklist):
        parameter = worklist.pop()

        if isinstance(parameter.value, int):
            evaluated[parameter.name] = parameter.value

        # If the value is a dictionary, it represents an expression gathered from HdlConvertor data.
        # Additionally, check if it's a width-specified value (e.g., "16'h5A5A"),
        # as resolve_ops is responsible for handling these cases as well.
        elif isinstance(parameter.value, dict) or re.match(
            r"\d+\'[hdob][\dabcdefABCDEF]+", parameter.value
        ):
            try:
                param_val = resolve_ops(parameter.value, evaluated, SimpleEval())
                if param_val is not None:
                    evaluated[parameter.name] = param_val
            except KeyError:
                worklist.appendleft(parameter)
                fail_count += 1
                continue
        else:
            try:
                evaluated[parameter.name] = simple_eval(parameter.value, names=evaluated)
            except (ValueError, SyntaxError, NameNotDefined):
                worklist.appendleft(parameter)
                fail_count += 1
                continue
        fail_count = 0

    if fail_count > 0:
        for parameter in worklist:
            invalid_parameters.append(parameter)

    return EvaluatedParamsReturnType(evaluated, invalid_parameters)


def _eval_param(
    val: Union[int, dict, str], params: Dict[str, Any], simpleeval_instance: SimpleEval
):
    """Function used to calculate parameter value.
    It is used for evaluating CONCAT and REPL_CONCAT in resolve_ops()"""

    if isinstance(val, int):
        return val
    if isinstance(val, dict) and val.keys() == {"value", "width"}:
        return val
    if isinstance(val, str):
        if val not in params.keys():
            keying = DEFAULT_FUNCTIONS.copy()
            for k in params.keys():
                keying[k] = params[k]
            return str(simple_eval(val, functions=keying))

        return _eval_param(params[val], params, simpleeval_instance)

    elif val["__class__"] == "HdlValueInt":
        value = int(val["val"], val["base"])
        if "bits" not in val.keys():
            return value
        else:
            return {"value": hex(value), "width": val["bits"]}

    elif val["__class__"] == "HdlOp":
        if val["fn"] == "CONCAT":
            bit_vector_l = _eval_param(val["ops"][0], params, simpleeval_instance)
            bit_vector_r = _eval_param(val["ops"][1], params, simpleeval_instance)
            bin_l = bin(int(bit_vector_l["value"], 16))[2:].zfill(bit_vector_l["width"])
            bin_r = bin(int(bit_vector_r["value"], 16))[2:].zfill(bit_vector_r["width"])
            return {
                "value": hex(int(bin_l + bin_r, 2)),
                "width": bit_vector_l["width"] + bit_vector_r["width"],
            }

        elif val["fn"] == "REPL_CONCAT":
            repeat = _eval_param(val["ops"][0], params, simpleeval_instance)
            bit_vector = _eval_param(val["ops"][1], params, simpleeval_instance)
            bin_val = bin(int(bit_vector["value"], 16))[2:].zfill(bit_vector["width"])
            return {"value": hex(int(repeat * bin_val, 2)), "width": repeat * bit_vector["width"]}

        else:
            simpleeval_instance.names = params
            return int(
                simpleeval_instance.eval(
                    _eval_param(
                        resolve_ops(val, params, simpleeval_instance), params, simpleeval_instance
                    ).replace("$", "")
                )
            )


def resolve_ops(
    val: Union[str, int, Dict[str, Any]], params: Dict[str, Any], simpleeval_instance: SimpleEval
):
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

    if isinstance(val, str):
        val = val.replace("$", "")

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
            "PART_SELECT_PRE": "-:",
        }

        if val["fn"] in bin_ops.keys():
            op = bin_ops[val["fn"]]
            left = resolve_ops(val["ops"][0], params, simpleeval_instance)
            right = resolve_ops(val["ops"][1], params, simpleeval_instance)
            if left is None or right is None:
                return None
            else:
                return f"({left}{op}{right})"

        elif val["fn"] == "TERNARY":
            cond = resolve_ops(val["ops"][0], params, simpleeval_instance)
            if_true = resolve_ops(val["ops"][1], params, simpleeval_instance)
            if_false = resolve_ops(val["ops"][2], params, simpleeval_instance)
            if cond is None or if_true is None or if_false is None:
                return None
            else:
                return f"({str(if_true)} if {str(cond)} else {str(if_false)})"

        elif val["fn"] in ["CONCAT", "REPL_CONCAT"]:
            # TODO - try to find a better way to get parameters default values
            # than copying params and evaluating them before each (REPL_)CONCAT
            params_cp = params.copy()
            for name in params_cp.keys():
                if isinstance(params_cp[name], str):
                    simpleeval_instance.names = params_cp
                    params_cp[name] = int(
                        simpleeval_instance.eval(params_cp[name].replace("$", ""))
                    )

            return _eval_param(val, params_cp, simpleeval_instance)

        elif val["fn"] == "PARAMETRIZATION":
            if (
                val["ops"][0] == "reg"
                and val["ops"][1]["__class__"] == "str"
                and val["ops"][1]["val"] is None
            ):
                # corner case - this happens in Verilog's output/input reg
                return "(0:0)"
            return resolve_ops(val["ops"][1], params, simpleeval_instance)

        elif val["fn"] == "INDEX":
            # this happens in VHDL's 'std_logic_vector({up_id DOWNTO low_id})
            # drop `std_logic_vector` and process the insides of parentheses
            if val["ops"][0] == "std_logic_vector":
                return resolve_ops(val["ops"][1], params, simpleeval_instance)
            else:
                return f"{val['ops'][0]}[{resolve_ops(val['ops'][1], params, simpleeval_instance)}]"
        elif val["fn"] == "CALL":
            args_str = ",".join(
                resolve_ops(str(arg), params, simpleeval_instance) for arg in val["ops"][1:]
            )

            return f"{resolve_ops(val['ops'][0], params, simpleeval_instance)}({args_str})"
        else:
            warning(f"resolve_ops: unhandled HdlOp function: {val['fn']}")
