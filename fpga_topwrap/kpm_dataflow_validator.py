# Copyright (C) 2023 Antmicro
# SPDX-License-Identifier: Apache-2.0
import re
import numexpr as ex
import json
from enum import Enum
from typing import NamedTuple, Union


class CheckStatus(Enum):
    OK = 0
    WARNING = 1
    ERROR = 2


class CheckResult(NamedTuple):
    status: CheckStatus
    message: Union[str, None]


def _check_duplicate_ip_names(data: bytes) -> CheckResult:
    """ Check for duplicate IP core names in the design.
    """
    dataflow_data = json.loads(data.decode())
    names_set = set()
    duplicates = set()
    for node in dataflow_data['nodes']:
        if node['name'] in names_set:
            duplicates.add(node['name'])
        else:
            names_set.add(node['name'])

    if not duplicates:
        return CheckResult(CheckStatus.OK, None)

    err_msg = f"Duplicate block names: {str(list(duplicates))}"
    return CheckResult(CheckStatus.ERROR, err_msg)


def _check_parameters_values(data: bytes) -> CheckResult:
    dataflow_data = json.loads(data.decode())
    invalid_params = list()

    for node in dataflow_data['nodes']:
        evaluated = dict()
        for [param_name, param_val] in node['options']:
            if not re.match(r"\d+\'[hdob][\dabcdefABCDEF]+", param_val):
                try:
                    evaluated[param_name] = int(
                        ex.evaluate(param_val, evaluated).take(0))
                except (ValueError, KeyError, SyntaxError, OverflowError):
                    invalid_params.append(f"{node['name']}:{param_name}")

    if invalid_params:
        err_msg = f"Invalid parameters values: {str(invalid_params)}"
        return CheckResult(CheckStatus.ERROR, err_msg)
    return CheckResult(CheckStatus.OK, None)


def _check_unconnected_interfaces(data: bytes) -> CheckResult:
    class Iface:
        def __init__(self, node_name: str, iface_name: str, iface_id: str):
            self.node_name = node_name
            self.iface_name = iface_name
            self.iface_id = iface_id

        def __repr__(self) -> str:
            return self.node_name + ":" + self.iface_name

        def __eq__(self, value: object) -> bool:
            if isinstance(value, Iface):
                return value.iface_id == self.iface_id
            return False

    dataflow_data = json.loads(data.decode())
    unconn_ifaces = []
    for node in dataflow_data['nodes']:
        for iface in node['interfaces']:
            unconn_ifaces.append(Iface(node['name'], iface[0], iface[1]['id']))

    for conn in dataflow_data['connections']:
        connected_ifaces = list(filter(
            lambda x: x.iface_id == conn['from'] or x.iface_id == conn['to'], unconn_ifaces)) # noqa
        for iface in connected_ifaces:
            unconn_ifaces.remove(iface)

    if unconn_ifaces:
        return CheckResult(
            CheckStatus.WARNING, f"Unconnected interfaces: {unconn_ifaces}")
    return CheckResult(CheckStatus.OK, None)


def validate_kpm_design(data: bytes, yamlfiles: list) -> dict:
    """ Run some checks to validate user-created design in KPM.
    Return a dict of warning and error messages to be sent to the KPM.
    """
    checks = [
        _check_duplicate_ip_names,
        _check_parameters_values,
        _check_unconnected_interfaces
    ]

    messages = {
        "errors": [],
        "warnings": []
    }
    for check in checks:
        status, msg = check(data)
        if status == CheckStatus.ERROR:
            messages["errors"].append("ERROR: " + msg)
        elif status == CheckStatus.WARNING:
            messages["warnings"].append("WARNING: " + msg)

    return messages
