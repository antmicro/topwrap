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
    packages=setuptools.find_packages(),
    install_requires=['pyyaml'],
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
