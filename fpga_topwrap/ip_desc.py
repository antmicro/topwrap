# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
from os import path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = path.join(path.dirname(__file__), "templates")


class IPCoreDescription:
    def __init__(self, name, parameters, ports, interfaces):
        if not isinstance(parameters, dict):
            raise TypeError(
                "'parameters' argument of IPCoreDescription "
                "shall be a dict with keys representing names "
                "of parameters"
            )
        if not isinstance(ports, dict):
            raise TypeError(
                "'ports' argument of IPCoreDescription shall be "
                "a dict with 'in' 'out' and 'inout' keys"
            )

        self.name = name
        self.parameters = parameters
        self.ports = ports
        self.interfaces = interfaces

    def save(self, filename=None):
        template_name = "ipcore_desc.j2.yml"
        env = Environment(
            loader=FileSystemLoader(searchpath=["./", TEMPLATES_DIR]),
        )
        template = env.get_template(template_name)

        text = template.render(
            parameters=self.parameters, ports=self.ports, interfaces=self.interfaces
        )
        if filename is None:
            filename = self.name + ".yml"
        f = open(filename, "w")
        f.write(text)

    def __repr__(self):
        return self.name
