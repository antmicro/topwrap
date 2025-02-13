# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
from dataclasses import dataclass
from typing import Iterator

from typing_extensions import override

from topwrap.backend.backend import Backend, BackendOutputInfo
from topwrap.backend.kpm.dataflow import KpmDataflowBackend
from topwrap.backend.kpm.specification import KpmSpecificationBackend
from topwrap.model.module import Module
from topwrap.util import JsonType


@dataclass
class KpmOutput:
    common_name: str
    specification: JsonType
    dataflow: JsonType


class KpmBackend(Backend[KpmOutput]):
    depth: int

    def __init__(self, depth: int = 0) -> None:
        super().__init__()
        self.depth = depth

    @override
    def represent(self, module: Module) -> KpmOutput:
        spec = KpmSpecificationBackend.default()
        spec.add_module(module, recursive=True)
        spec = spec.build()
        flow = KpmDataflowBackend(spec)
        if module.design is not None:
            flow.represent_design(module.design, depth=self.depth)
        flow = flow.build()

        return KpmOutput(specification=spec, dataflow=flow, common_name=module.id.combined())

    @override
    def serialize(self, repr: KpmOutput) -> Iterator[BackendOutputInfo]:
        yield BackendOutputInfo(
            content=json.dumps(repr.specification), filename=f"{repr.common_name}_spec.json"
        )
        yield BackendOutputInfo(
            content=json.dumps(repr.dataflow), filename=f"{repr.common_name}_flow.json"
        )
