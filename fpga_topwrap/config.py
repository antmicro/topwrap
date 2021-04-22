# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0


class Config:
    def __init__(self, force_interface_compliance=False):
        self.force_interface_compliance = force_interface_compliance


config = Config()
