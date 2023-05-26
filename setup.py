#!/usr/bin/env python3
# coding: utf-8
#
# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0

import setuptools

entry_points = {
    'console_scripts': [
        'fpga_topwrap = fpga_topwrap.cli:main',
    ]
}

setuptools.setup(
    name="fpga_topwrap",
    version="0.0.1",
    author="Antmicro",
    description="IP Core wrapper",
    packages=setuptools.find_namespace_packages(),
    install_requires=[
        'PyYAML',
        'click',
        'amaranth-yosys',
        'edalize==0.4.0',
        'fusesoc==1.12.0',
        'amaranth @ git+https://github.com/amaranth-lang/amaranth',
        'wasmtime==1.0.1',
        'numexpr',
        'pipeline_manager_backend_communication @ git+https://github.com/antmicro/kenning-pipeline-manager-backend-communication'
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    include_package_data=True,
    zip_safe=False,
    entry_points=entry_points,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
