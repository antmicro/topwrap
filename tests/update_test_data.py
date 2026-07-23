# Copyright (c) 2025-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from pathlib import Path

import cyclopts
from tests_kpm.conftest import all_design_paths, test_dirs_data

from topwrap.backend.kpm.backend import KpmBackend
from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.backend.yaml.backend import IpCoreDescriptionBackend
from topwrap.backend.yaml.interface import InterfaceDefinitionDescriptionBackend
from topwrap.frontend.yaml.frontend import YamlFrontend
from topwrap.util import save_file_to_json

cli = cyclopts.App()


def update_dataflows():
    test_dirs = test_dirs_data()
    for example_name, design in all_design_paths().items():
        frontend = YamlFrontend()
        out = frontend.parse_files([design])
        design_module = out.modules[0]
        design_module.design.update_interconnects_from_memory_maps()

        backend = KpmBackend(depth=-1)
        repr = backend.represent(design_module)

        save_file_to_json(
            test_dirs[example_name],
            f"dataflow_{example_name}.json",
            repr.dataflow,
        )


def update_specifications():
    test_dirs = test_dirs_data()
    for example_name, design in all_design_paths().items():
        frontend = YamlFrontend()
        out = frontend.parse_files([design])
        design_module = out.modules[0]
        design_module.design.update_interconnects_from_memory_maps()

        spec = KpmSpecificationBackend.default()
        spec.add_module(design_module, recursive=True)
        spec = spec.build()

        save_file_to_json(
            test_dirs[example_name],
            f"specification_{example_name}.json",
            spec,
        )


def update_json_ipcore_iface():
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.dirname(SCRIPT_DIR))
    from examples.ir_examples.modules import (
        adv_top,
        hier_top,
        intf_top,
        intr_top,
        inv_top,
        simp_top,
    )

    ip_core_dir = Path("data/data_yaml/ipcore")
    ip_core_dir.mkdir(parents=True, exist_ok=True)

    ifaces_dir = Path("data/data_yaml/ifaces")
    ifaces_dir.mkdir(parents=True, exist_ok=True)

    irs = [
        adv_top,
        hier_top,
        intf_top,
        intr_top,
        inv_top,
        simp_top,
    ]
    for ir in irs:
        for iface in ir.interfaces:
            definition = iface.definition
            desc = InterfaceDefinitionDescriptionBackend().represent(definition)
            desc.save(ifaces_dir / f"{definition.id.combined()}.yaml")
        backend = IpCoreDescriptionBackend()
        repr = backend.represent(ir)
        files = backend.serialize(repr)
        ip_core = next(files)
        ip_core.save(ip_core_dir)


@cli.default
def update_test_data(
    *, dataflow: bool = False, specification: bool = False, ipcore_and_iface_json: bool = False
):
    if dataflow:
        update_dataflows()

    if specification:
        update_specifications()

    if ipcore_and_iface_json:
        update_json_ipcore_iface()


if __name__ == "__main__":
    cli()
