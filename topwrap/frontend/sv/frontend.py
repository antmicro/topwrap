# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Iterable, Iterator, Union

from pyslang import DiagnosticSeverity, SourceLocation, SyntaxTree

from topwrap.frontend.frontend import Frontend, FrontendParseStrInput
from topwrap.frontend.sv.module import SystemVerilogSlangParser
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module


class SystemVerilogFrontend(Frontend):
    def __init__(
        self,
        modules: Iterable[Module] = (),
        interfaces: Iterable[InterfaceDefinition] = (),
        diag_level: DiagnosticSeverity = DiagnosticSeverity.Warning,
    ) -> None:
        super().__init__(modules, interfaces)
        self.diag_level = diag_level

    def _parser_instance(self) -> SystemVerilogSlangParser:
        return SystemVerilogSlangParser(
            diag_log_level=self.diag_level, modules=self.modules, interfaces=self.interfaces
        )

    def parse_str(self, sources: Iterable[Union[str, FrontendParseStrInput]]) -> Iterator[Module]:
        buffers = []
        inst = self._parser_instance()
        for src in sources:
            cnt = src if isinstance(src, str) else src.content
            buffers.append(buf := inst.src_man.assignText(cnt))
            if isinstance(src, FrontendParseStrInput):
                inst.src_man.addLineDirective(SourceLocation(buf.id, 0), 2, src.name, 0)
        tree = SyntaxTree.fromBuffers(buffers, inst.src_man)

        yield from inst.parse_tree(tree)

    def parse_files(self, sources: Iterable[Path]) -> Iterator[Module]:
        s_sources = [str(p) for p in sources]
        inst = self._parser_instance()
        tree = SyntaxTree.fromFiles(s_sources, inst.src_man)

        yield from inst.parse_tree(tree)
