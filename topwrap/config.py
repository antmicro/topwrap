# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0


class Config:
    """Configuration class used to store global choices
    for behavior of Topwrap.
    """

    def __init__(self, force_interface_compliance=False):
        self.force_interface_compliance = force_interface_compliance


config = Config()
