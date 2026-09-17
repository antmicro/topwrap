# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from typing import Iterable, Union

from pyslang import Bag, PreprocessorOptions, SourceLocation, SyntaxTree

from topwrap.frontend.frontend import (
    Frontend,
    FrontendApproach,
    FrontendMetadata,
    FrontendParseException,
    FrontendParseOutput,
    FrontendParseStrInput,
)
from topwrap.frontend.sv.module import SystemVerilogSlangParser
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.module import Module

logger = logging.getLogger(__name__)


class SystemVerilogFrontend(Frontend):
    def __init__(
        self,
        modules: Iterable[Module] = (),
        interfaces: Iterable[InterfaceDefinition] = (),
        approach: FrontendApproach = FrontendApproach.STRICT,
    ) -> None:
        super().__init__(modules, interfaces, approach)

    @property
    def metadata(self):
        return FrontendMetadata(name="systemverilog", file_association=[".sv", ".svh", ".v", ".vh"])

    def _parser_instance(self) -> SystemVerilogSlangParser:
        return SystemVerilogSlangParser(modules=self.modules, interfaces=self.interfaces)

    def _parse_tree(self, inst: SystemVerilogSlangParser, tree: SyntaxTree) -> FrontendParseOutput:
        modules, interfaces, warnings, errors = inst.parse_tree(tree)

        for warning in warnings:
            logger.warning(warning)

        if errors and self.approach == FrontendApproach.STRICT:
            raise FrontendParseException("\n".join(errors))
        for error in errors:
            logger.error(error)

        return FrontendParseOutput(modules=modules, interfaces=interfaces)

    def parse_str(
        self, sources: Iterable[Union[str, FrontendParseStrInput]]
    ) -> FrontendParseOutput:
        buffers = []
        inst = self._parser_instance()
        for src in sources:
            cnt = src if isinstance(src, str) else src.content
            buffers.append(buf := inst.src_man.assignText(cnt))
            if isinstance(src, FrontendParseStrInput):
                inst.src_man.addLineDirective(SourceLocation(buf.id, 0), 2, src.name, 0)
        tree = SyntaxTree.fromBuffers(buffers, inst.src_man)

        return self._parse_tree(inst, tree)

    def parse_files(
        self,
        sources: Iterable[Path],
        *,
        include_dirs: Iterable[Path] = (),
        defines: Iterable[str] = (),
    ) -> FrontendParseOutput:
        s_sources = [str(p) for p in sources]
        inst = self._parser_instance()
        options = None
        inc_dirs = [str(p) for p in include_dirs]
        macros = list(defines)
        if inc_dirs or macros:
            options = Bag()
            preproc = PreprocessorOptions()
            preproc.additionalIncludePaths = inc_dirs
            preproc.predefines = macros
            options.preprocessorOptions = preproc
        if len(s_sources) > 0:
            tree = (
                SyntaxTree.fromFiles(s_sources, inst.src_man, options)
                if options is not None
                else SyntaxTree.fromFiles(s_sources, inst.src_man)
            )
            return self._parse_tree(inst, tree)

        return FrontendParseOutput(modules=[], interfaces=[])
