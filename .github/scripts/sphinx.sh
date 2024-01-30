#!/usr/bin/env sh
# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


set -e

cd $(dirname $0)/../../docs

pip3 install -r requirements.txt

make html latex
