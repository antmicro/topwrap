#!/usr/bin/env python3
# coding: utf-8
#
# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import setuptools

entry_points = {
    "console_scripts": [
        "fpga_topwrap = fpga_topwrap.cli:main",
    ]
}

setuptools.setup(
    name="fpga_topwrap",
    version="0.0.1",
    author="Antmicro",
    description="IP Core wrapper",
    packages=setuptools.find_namespace_packages(),
    install_requires=[
        "PyYAML",
        "click",
        "amaranth-yosys",
        "amaranth==0.4.0.*",
        "wasmtime==1.0.1",
        "numexpr",
        "hdlConvertor @ git+https://github.com/Nic30/hdlConvertor.git",
        "pipeline_manager_backend_communication @ git+https://github.com/antmicro/kenning-pipeline-manager-backend-communication@06b38824500d8239432e614bfa655d8e50b197cf",
        "pipeline_manager @ git+https://github.com/antmicro/kenning-pipeline-manager@686c4592c4e816a72116107abaf8a55dec0ed5a1",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-lazy-fixtures"],
    include_package_data=True,
    zip_safe=False,
    entry_points=entry_points,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
