# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Union, cast

import pyslang as ps

from topwrap.backend.sv.common import sv_varname
from topwrap.model.connections import (
    Connection,
    ConstantConnection,
    Port,
    PortConnection,
    PortDirection,
    ReferencedPort,
)
from topwrap.model.design import Design, ModuleInstance
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    BitStruct,
    Dimensions,
    Enum,
    Logic,
    LogicArray,
    StructField,
    has_symbolic_dimensions,
)
from topwrap.model.interface import (
    Interface,
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, FileReference, Identifier, ObjectId, Parameter
from topwrap.model.module import Module
from topwrap.util import MISSING, is_simple_sv_literal

logger = logging.getLogger(__name__)


def _slang_dir_to_ir_dir(dir: ps.ArgumentDirection) -> PortDirection:
    return {
        ps.ArgumentDirection.In: PortDirection.IN,
        ps.ArgumentDirection.InOut: PortDirection.INOUT,
        ps.ArgumentDirection.Out: PortDirection.OUT,
    }[dir]


def _infer_modports(modports: Iterable[str]) -> dict[InterfaceMode, str]:
    """
    Tries to find the manager and subordinate in an iterable of arbitrary
    modports using their names
    """

    M, S = InterfaceMode.MANAGER, InterfaceMode.SUBORDINATE
    terms = [
        ("manager", M), ("subordinate", S), ("master", M), ("slave", S), ("initiator", M),
        ("target", S), ("driver", M), ("peripheral", S), ("controller", M), ("worker", S),
        ("responder", S), ("server", M), ("client", S), ("producer", M), ("consumer", S),
        ("bottom", S), ("mst", M), ("slv", S), ("mgr", M), ("drv", M), ("rsp", S), ("srv", M),
        ("ctrl", M), ("man", M), ("tx", M), ("rx", S), ("sub", S), ("resp", S), ("init", M),
    ]  # fmt: skip
    exact_terms = [("top", M), ("out", M), ("in", S), ("m", M), ("s", S)]

    cands: dict[InterfaceMode, list[tuple[int, str]]] = {
        InterfaceMode.MANAGER: [],
        InterfaceMode.SUBORDINATE: [],
    }

    for modport in modports:
        for exact, term_group in (
            (False, enumerate(terms)),
            (True, enumerate(exact_terms, len(terms))),
        ):
            for i, (term, side) in term_group:
                if exact and term == modport.lower() or not exact and term in modport.lower():
                    cands[side].append((i, modport))
                    break

    for mps in cands.values():
        mps.sort()

    res = dict[InterfaceMode, str]()
    for side in (InterfaceMode.MANAGER, InterfaceMode.SUBORDINATE):
        if cands[side] != []:
            res[side] = cands[side][0][1]
    return res


def _ir_id_to_sv_str(id: Identifier) -> str:
    """
    Extended IR identifiers (vendor, library) can't be natively
    represented in SystemVerilog. For the purpose of finding
    modules/interfaces that already are loaded in the IR, only
    the name part will be used.
    """

    return sv_varname(id.name)


def _strip_sv_comments(text: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    lines = []
    for ln in no_block.splitlines():
        ln = ln.split("//", 1)[0].strip()
        if ln:
            lines.append(ln)
    return " ".join(lines).strip()


def _lookup_name_from_clean_alias(cleaned_name: str, fallback_name: str) -> str:
    lookup_name = cleaned_name
    if "[" in lookup_name:
        lookup_name = lookup_name.split("[", 1)[0].strip()
    if lookup_name:
        return lookup_name
    toks = re.findall(r"[A-Za-z_$\\][A-Za-z0-9_$:\\\\]*", cleaned_name)
    if toks:
        return toks[-1]
    return cleaned_name if cleaned_name else fallback_name


def _extract_dims_from_alias_text(cleaned_name: str) -> list[Dimensions]:
    dims: list[Dimensions] = []
    if "[" not in cleaned_name:
        return dims
    dim_tail = cleaned_name[cleaned_name.find("[") :]
    for m in re.finditer(r"\[(?P<left>[^\]:]+)(?::(?P<right>[^\]]+))?\]", dim_tail):
        left = m.group("left").strip()
        right = m.group("right")
        if right is None:
            dims.append(Dimensions(upper=ElaboratableValue(left) - ElaboratableValue(1)))
            continue
        dims.append(
            Dimensions(
                upper=ElaboratableValue(left),
                lower=ElaboratableValue(right.strip()),
            )
        )
    return dims


def _logic_with_dims(item: Logic, dims: list[Dimensions]) -> Logic:
    return LogicArray(item=item, dimensions=dims) if dims else item


class _ModuleAstParserState:
    def __init__(
        self, parser: "SystemVerilogSlangParser", mod_ast: ps.InstanceSymbol, comp: ps.Compilation
    ) -> None:
        self.parser = parser
        self.mod_ast = mod_ast
        self.comp = comp
        self._STMT_ASSIGN_CHECKERS: dict[type, Any] = {}
        self._cycle_reported: set[tuple[str, Optional[tuple[int, int]]]] = set()
        self._instance_output_sources_by_name_cache: Optional[dict[str, list[ReferencedPort]]] = (
            None
        )
        self._instance_port_expr_text_cache: dict[ps.InstanceSymbol, dict[str, str]] = {}
        self._member_expr_types: tuple[type, ...] = ()
        self._module_text_for_port_scan = ""
        self._port_expr_re: re.Pattern[str] = re.compile(r"$^")
        self._resolve_cache: dict[
            tuple[str, Optional[tuple[int, int]]],
            tuple[list[Union[ReferencedPort, ElaboratableValue]], bool],
        ] = {}
        self._resolving: set[tuple[str, Optional[tuple[int, int]]]] = set()
        self._select_cache: dict[str, ReferencedPort] = {}
        self.am: ps.AnalysisManager = cast(ps.AnalysisManager, None)
        self.bb_mod: Module = cast(Module, None)
        self.bb_ports: dict[str, Port] = {}
        self.components: list[ModuleInstance] = []
        self.concat_idx = 0
        self.connections: list[Union[PortConnection, ConstantConnection]] = []
        self.cont_assign_map: dict[ps.Symbol, list[ps.Expression]] = {}
        self.cont_assign_text_map: dict[ps.Symbol, list[str]] = {}
        self.inst_port_conns: dict[ps.InstanceSymbol, list[ps.PortConnection]] = {}
        self.instance_map: dict[ps.InstanceSymbol, ModuleInstance] = {}
        self.instance_output_sources: dict[ps.InstanceSymbol, list[tuple[ps.Symbol, Port]]] = {}
        self.logic_inst: Optional[ModuleInstance] = None
        self.mod: Module = cast(Module, None)
        self.name_to_instance_ports: dict[str, list[ReferencedPort]] = {}
        self.ports_by_name: dict[str, ps.PortSymbol] = {}
        self.ports_by_norm_name: dict[str, ps.PortSymbol] = {}
        self.procedural_assignments: dict[str, list[ps.Expression]] = {}
        self.sym_by_name: dict[str, ps.Symbol] = {}
        self.sym_by_norm_name: dict[str, ps.Symbol] = {}
        self.sym_ports: dict[ps.Symbol, Port] = {}
        self.sym_to_instance_ports: dict[ps.Symbol, list[ReferencedPort]] = {}

    class _ConcatRun:
        def __init__(self) -> None:
            self.items: list[dict[str, Any]] = []
            self.base: Optional[ps.Symbol] = None
            self.step: Optional[int] = None

        def reset(self) -> None:
            self.items = []
            self.base = None
            self.step = None

        def add(self, span: dict[str, Any]) -> bool:
            if not self.items:
                self.base = span["base"]
                self.items = [span]
                self.step = None
                return True
            if span["base"] is not self.base:
                return False
            prev = self.items[-1]
            if self.step is not None and prev["dir"] not in (0, self.step):
                return False
            delta = span["start"] - prev["end"]
            if self.step is None:
                if delta not in (1, -1):
                    return False
                self.step = delta
            if delta != self.step:
                return False
            if span["dir"] not in (0, self.step):
                return False
            self.items.append(span)
            return True

    class _CombState:
        __slots__ = ("sources", "proc_logic", "assignments")

        def __init__(self) -> None:
            self.sources: list[Union[ReferencedPort, ElaboratableValue]] = []
            self.proc_logic = False
            self.assignments = 0

    def _norm_sv_ident(self, name: str) -> str:
        out = name.strip()
        if out.startswith("\\"):
            out = out[1:].strip()
        return out

    def _expr_identifier_name(self, text: str) -> Optional[str]:
        txt = text.strip()
        if txt == "":
            return None
        if txt.startswith("\\"):
            esc = txt[1:]
            m = re.match("(?P<id>\\S+)", esc)
            return m.group("id") if m is not None else None
        if re.fullmatch("[A-Za-z_$][A-Za-z0-9_$]*", txt):
            return txt
        return None

    def _get_concat_module(self, inputs: int) -> Module:
        mod = self.parser._concat_modules.get(inputs)
        if mod is None:
            ports = [Port(name=f"in{i}", direction=PortDirection.IN) for i in range(inputs)]
            ports.append(Port(name="out", direction=PortDirection.OUT))
            mod = Module(id=Identifier(name=f"concat_{inputs}"), ports=ports)
            self.parser._concat_modules[inputs] = mod
        return mod

    def _get_select_module(self, select_name: str) -> Module:
        """
        Get or create a select module for bit-select or range-select operations.
        The select_name identifies the specific select operation (e.g., "var[3:1]").
        The module has an input 'var' (the source) and an output named after the
        select (the selected portion).
        """
        mod = self.parser._select_modules.get(select_name)
        if mod is None:
            var_name = select_name.split("[")[0]
            ports = [
                Port(name=var_name, direction=PortDirection.IN),
                Port(name=select_name, direction=PortDirection.OUT),
            ]
            mod = Module(id=Identifier(name=select_name), ports=ports)
            self.parser._select_modules[select_name] = mod
        return mod

    def _token_text(self, token: Any) -> Optional[str]:
        if token is None:
            return None
        return (
            getattr(token, "value", None) or getattr(token, "valueText", None) or str(token).strip()
        )

    def _lookup_symbol_by_name(self, name: Optional[str]) -> Optional[ps.Symbol]:
        if name is None:
            return None
        if (hit := (self.ports_by_name.get(name) or self.sym_by_name.get(name))) is not None:
            return hit
        norm = self._norm_sv_ident(name)
        return self.ports_by_norm_name.get(norm) or self.sym_by_norm_name.get(norm)

    def _base_symbol_from_syntax(self, expr: Optional[ps.Expression]) -> Optional[ps.Symbol]:
        if expr is None:
            return None
        syntax = getattr(expr, "syntax", None)
        if isinstance(syntax, ps.IdentifierSelectNameSyntax):
            base = self._token_text(getattr(syntax, "identifier", None))
            return self._lookup_symbol_by_name(base)
        return None

    def _param_expr_str(
        self, expr: Any, genvar_map: dict[str, int], allowed_names: Optional[set[str]] = None
    ) -> Optional[str]:
        if expr is None:
            return None
        if isinstance(expr, ps.NamedValueExpression):
            sym = getattr(expr, "symbol", None)
            name = getattr(sym, "name", None)
            if name is not None and name in genvar_map:
                return str(genvar_map[name])
            if allowed_names is not None and name is not None and (name not in allowed_names):
                return None
            return str(sym.name) if sym is not None else str(expr).strip()
        if isinstance(expr, ps.IdentifierNameSyntax):
            name = self._token_text(expr.identifier)
            if name is not None and name in genvar_map:
                return str(genvar_map[name])
            if allowed_names is not None and name is not None and (name not in allowed_names):
                return None
            return name or str(expr).strip()
        if isinstance(expr, ps.IdentifierSelectNameSyntax):
            base = self._token_text(expr.identifier) or str(expr.identifier).strip()
            if allowed_names is not None and base not in allowed_names and ("::" not in base):
                return None
            for selector in expr.selectors:
                if isinstance(selector, ps.ElementSelectSyntax):
                    bit_sel = selector.selector
                    idx_expr = getattr(bit_sel, "expr", None)
                    idx_str = self._param_expr_str(idx_expr, genvar_map, allowed_names)
                    if idx_str is None:
                        idx_str = str(bit_sel).strip()
                    base = f"{base}[{idx_str}]"
                else:
                    base = f"{base}{str(selector).strip()}"
            return base
        if isinstance(expr, ps.ElementSelectExpression):
            base = (
                self._param_expr_str(expr.value, genvar_map, allowed_names)
                or str(expr.value).strip()
            )
            idx = (
                self._param_expr_str(expr.selector, genvar_map, allowed_names)
                or str(expr.selector).strip()
            )
            return f"{base}[{idx}]"
        if isinstance(expr, ps.RangeSelectExpression):
            base = (
                self._param_expr_str(expr.value, genvar_map, allowed_names)
                or str(expr.value).strip()
            )
            left = (
                self._param_expr_str(expr.left, genvar_map, allowed_names) or str(expr.left).strip()
            )
            right = (
                self._param_expr_str(expr.right, genvar_map, allowed_names)
                or str(expr.right).strip()
            )
            selection_kind = getattr(expr, "selectionKind", None)
            if selection_kind == ps.RangeSelectionKind.IndexedUp:
                return f"{base}[{left}+:{right}]"
            if selection_kind == ps.RangeSelectionKind.IndexedDown:
                return f"{base}[{left}-:{right}]"
            return f"{base}[{left}:{right}]"
        if isinstance(expr, ps.ParenthesizedExpressionSyntax):
            inner = (
                self._param_expr_str(expr.expression, genvar_map, allowed_names)
                or str(expr.expression).strip()
            )
            return f"({inner})"
        return str(expr).strip()

    def _instance_param_overrides(
        self, inst_sym: ps.InstanceSymbol, child_mod: Module, genvar_map: dict[str, int]
    ) -> dict[ObjectId[Parameter], ElaboratableValue]:
        syntax = getattr(inst_sym, "syntax", None)
        parent = getattr(syntax, "parent", None) if syntax is not None else None
        params = getattr(parent, "parameters", None) if parent is not None else None
        param_list = getattr(params, "parameters", None) if params is not None else None
        if param_list is None:
            return {}
        allowed_names = {p.name for p in self.mod.parameters}
        overrides: dict[ObjectId[Parameter], ElaboratableValue] = {}
        ordered_idx = 0
        for param in param_list:
            if not isinstance(param, ps.ParamAssignmentSyntax):
                continue
            if isinstance(param, ps.OrderedParamAssignmentSyntax):
                if ordered_idx >= len(child_mod.parameters):
                    ordered_idx += 1
                    continue
                param_def = child_mod.parameters[ordered_idx]
                ordered_idx += 1
                expr = getattr(param, "expr", None)
                expr_str = self._param_expr_str(expr, genvar_map, allowed_names)
                if expr_str is None:
                    continue
                overrides[param_def._id] = ElaboratableValue(expr_str)
            elif isinstance(param, ps.NamedParamAssignmentSyntax):
                name = getattr(param, "name", None)
                pname = getattr(name, "value", None) if name is not None else None
                if pname is None and name is not None:
                    pname = str(name).strip()
                if pname is None:
                    continue
                param_def = child_mod.parameters.find_by_name(pname)
                if param_def is None:
                    continue
                expr = getattr(param, "expr", None)
                expr_str = self._param_expr_str(expr, genvar_map, allowed_names)
                if expr_str is None:
                    continue
                overrides[param_def._id] = ElaboratableValue(expr_str)
        return overrides

    def _collect_instances(
        self,
        scope: Iterable[ps.Symbol],
        name_suffix: str = "",
        genvar_map: Optional[dict[str, int]] = None,
    ) -> None:
        """Recursively collect module instances from a scope, including generate blocks."""
        genvar_map = {} if genvar_map is None else genvar_map
        for entry in scope:
            if isinstance(entry, ps.GenerateBlockArraySymbol):
                gen_name = self._token_text(getattr(entry.syntax, "identifier", None))
                for block in entry.entries:
                    if isinstance(block, ps.GenerateBlockSymbol):
                        block_suffix = f"{name_suffix}#{block.arrayIndex}"
                        block_genvars = dict(genvar_map)
                        if gen_name is not None:
                            block_genvars[gen_name] = int(block.arrayIndex)
                        self._collect_instances(block, block_suffix, block_genvars)
            elif isinstance(entry, ps.GenerateBlockSymbol):
                self._collect_instances(entry, name_suffix, genvar_map)
            elif isinstance(entry, ps.InstanceSymbol) and entry.isModule:
                self.parser._visit_instance_ast(entry, self.comp, False)
                child_mod = self.parser._submodules[entry.body.name]
                inst_name = f"{entry.name}{name_suffix}"
                params = self._instance_param_overrides(entry, child_mod, genvar_map)
                inst = ModuleInstance(name=inst_name, module=child_mod, parameters=params)
                self.components.append(inst)
                self.instance_map[entry] = inst
                self.inst_port_conns[entry] = list(entry.portConnections)

    def _is_member_access(self, expr: Any) -> bool:
        if self._member_expr_types and isinstance(expr, self._member_expr_types):
            return True
        return hasattr(expr, "member") and hasattr(expr, "value")

    def _expr_symbol(self, expr: Optional[ps.Expression]) -> Optional[ps.Symbol]:
        if expr is None:
            return None
        if isinstance(expr, ps.NamedValueExpression):
            base_sym = self._base_symbol_from_syntax(expr)
            if base_sym is not None:
                return base_sym
            return expr.symbol
        if isinstance(expr, ps.ConversionExpression):
            operand = getattr(expr, "operand", None)
            return self._expr_symbol(operand) if isinstance(operand, ps.Expression) else None
        if isinstance(expr, (ps.ElementSelectExpression, ps.RangeSelectExpression)):
            return self._expr_symbol(expr.value)
        if self._is_member_access(expr):
            base = getattr(expr, "value", None)
            if isinstance(base, ps.Expression):
                return self._expr_symbol(base)
            sym = getattr(base, "symbol", None)
            if sym is not None:
                return sym
            return self._expr_symbol(base) if base is not None else None
        if isinstance(expr, ps.AssignmentExpression):
            for side in (expr.right, expr.left):
                sym = self._expr_symbol(side)
                if sym is not None:
                    return sym
        return None

    def _raw_source_for_node(self, node: Any) -> str:
        rng = getattr(node, "sourceRange", None)
        if rng is None:
            syn = getattr(node, "syntax", None)
            rng = getattr(syn, "sourceRange", None) if syn is not None else None
        if rng is None:
            return ""
        try:
            src = self.parser.src_man.getSourceText(rng.start.buffer)
            return src[rng.start.offset : rng.end.offset]
        except Exception:
            return ""

    def _walk_procedural_stmts(self, stmt: Optional[ps.Statement]) -> None:
        if stmt is None:
            return
        if isinstance(stmt, ps.ExpressionStatement):
            expr = stmt.expr
            if isinstance(expr, ps.AssignmentExpression):
                lhs = expr.left
                lhs_sym = self._expr_symbol(lhs)
                if lhs_sym is not None:
                    lhs_name = getattr(lhs_sym, "name", None)
                    if isinstance(lhs_name, str):
                        self.procedural_assignments.setdefault(lhs_name, []).append(expr.right)
        for attr in ("stmt", "body", "ifTrue", "ifFalse", "elseClause", "list", "statements"):
            child = getattr(stmt, attr, None)
            if isinstance(child, list):
                for entry in child:
                    if isinstance(entry, ps.Statement):
                        self._walk_procedural_stmts(entry)
            elif isinstance(child, ps.Statement):
                self._walk_procedural_stmts(child)
            else:
                child_list = getattr(child, "list", None)
                if isinstance(child_list, list):
                    for entry in child_list:
                        if isinstance(entry, ps.Statement):
                            self._walk_procedural_stmts(entry)

    def _cache_instance_outputs(self) -> None:
        for inst_sym, inst in self.instance_map.items():
            child_mod = inst.module
            outputs: list[tuple[ps.Symbol, Port]] = []
            for pc in self.inst_port_conns.get(inst_sym, []):
                child_port = child_mod.ports.find_by_name(pc.port.name)
                if child_port is None:
                    continue
                if child_port.direction not in (PortDirection.OUT, PortDirection.INOUT):
                    continue
                expr_sym = self._expr_symbol(pc.expression)
                if expr_sym is None:
                    expr_txt = str(getattr(pc.expression, "syntax", "")).strip()
                    if expr_txt == "":
                        rng = getattr(pc.expression, "sourceRange", None)
                        if rng is not None:
                            try:
                                src = self.parser.src_man.getSourceText(rng.start.buffer)
                                expr_txt = src[rng.start.offset : rng.end.offset].strip()
                            except Exception:
                                expr_txt = ""
                    if expr_txt == "":
                        expr_txt = (
                            self._raw_instance_port_expr(inst_sym, pc.port.name) or ""
                        ).strip()
                    expr_name = self._expr_identifier_name(expr_txt)
                    if expr_name is not None:
                        expr_sym = self._lookup_symbol_by_name(expr_name)
                        if expr_sym is None:
                            self.name_to_instance_ports.setdefault(expr_name, []).append(
                                ReferencedPort(instance=inst, io=child_port)
                            )
                if expr_sym is None:
                    continue
                outputs.append((expr_sym, child_port))
                ref = ReferencedPort(instance=inst, io=child_port)
                self.sym_to_instance_ports.setdefault(expr_sym, []).append(ref)
                expr_name = getattr(expr_sym, "name", None)
                if isinstance(expr_name, str):
                    self.name_to_instance_ports.setdefault(expr_name, []).append(ref)
            self.instance_output_sources[inst_sym] = outputs

    def _extract_port_exprs(self, snippet: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for m in self._port_expr_re.finditer(snippet):
            name = m.group("name")
            if name.startswith("\\"):
                name = name[1:]
            out.setdefault(name, m.group("expr").strip())
        return out

    def _find_instance_port_block(self, text: str, inst_name: str) -> Optional[str]:
        for m in re.finditer(re.escape(inst_name), text):
            start = m.start()
            end = m.end()
            prev = text[start - 1] if start > 0 else " "
            nxt = text[end] if end < len(text) else " "
            if re.match("[A-Za-z0-9_.$\\\\]", prev) or re.match("[A-Za-z0-9_$]", nxt):
                continue
            k = end
            while k < len(text) and text[k].isspace():
                k += 1
            if k >= len(text) or text[k] != "(":
                continue
            depth = 0
            close_idx = -1
            for i in range(k, len(text)):
                ch = text[i]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth != 0:
                        continue
                    j = i + 1
                    while j < len(text) and text[j].isspace():
                        j += 1
                    if j < len(text) and text[j] == ";":
                        close_idx = i
                    break
            if close_idx != -1:
                return text[k + 1 : close_idx]
        return None

    def _build_instance_port_expr_cache(self, inst_sym: ps.InstanceSymbol) -> dict[str, str]:
        cached: dict[str, str] = {}
        syn = getattr(inst_sym, "syntax", None)
        rng = getattr(syn, "sourceRange", None) if syn is not None else None
        if rng is not None:
            try:
                src = self.parser.src_man.getSourceText(rng.start.buffer)
                snippet = src[rng.start.offset : rng.end.offset]
                cached.update(self._extract_port_exprs(snippet))
            except Exception:
                pass
        if (
            cached
            or not self._module_text_for_port_scan
            or len(self._module_text_for_port_scan) > 200000
        ):
            return cached
        inst_name = str(getattr(inst_sym, "name", "")).strip()
        snippet = self._find_instance_port_block(self._module_text_for_port_scan, inst_name)
        if snippet is None:
            return cached
        cached.update(self._extract_port_exprs(snippet))
        return cached

    def _raw_instance_port_expr(self, inst_sym: ps.InstanceSymbol, port_name: str) -> Optional[str]:
        cached = self._instance_port_expr_text_cache.get(inst_sym)
        if cached is None:
            cached = self._build_instance_port_expr_cache(inst_sym)
            self._instance_port_expr_text_cache[inst_sym] = cached
        return cached.get(port_name)

    def _expr_constant(self, expr: Optional[ps.Expression]) -> Optional[ElaboratableValue]:
        if expr is None:
            return None
        const_val = expr.constant
        if const_val is not None:
            if getattr(const_val, "bad", False):
                logger.error("Bad constant expression: %s", expr.syntax)
                return None
            return ElaboratableValue(str(const_val).strip())
        if isinstance(expr, (ps.IntegerLiteral, ps.UnbasedUnsizedIntegerLiteral)):
            syn = getattr(expr, "syntax", None)
            return ElaboratableValue(str(syn if syn is not None else expr).strip())
        return None

    def _expr_index_and_str(self, expr: ps.Expression) -> tuple[Optional[int], str]:
        def _parse_sv_int_literal(text: str) -> Optional[int]:
            s = text.strip().replace("_", "")
            if s == "":
                return None
            sign = 1
            if s[0] in "+-":
                if s[0] == "-":
                    sign = -1
                s = s[1:]
            if s == "":
                return None
            if "'" not in s:
                if re.fullmatch("\\d+", s):
                    return sign * int(s, 10)
                return None
            m = re.fullmatch("(?:\\d+)?'[sS]?([bBdDhHoO])([0-9a-fA-FxXzZ?]+)", s)
            if m is None:
                return None
            base_ch = m.group(1).lower()
            digits = m.group(2)
            if re.search("[xXzZ?]", digits):
                return None
            base = {"b": 2, "o": 8, "d": 10, "h": 16}[base_ch]
            try:
                return sign * int(digits, base)
            except ValueError:
                return None

        const_val = self._expr_constant(expr)
        if const_val is not None:
            const_str = str(const_val.value)
            parsed = _parse_sv_int_literal(const_str)
            if parsed is not None:
                return (parsed, str(parsed))
            try:
                return (int(const_val.value), const_str)
            except (ValueError, TypeError):
                return (None, const_str)
        syntax = expr.syntax
        return (None, str(syntax) if syntax else "?")

    def _packed_outer_index_pos(self, sym: ps.Symbol, idx: int) -> Optional[tuple[int, int]]:
        sym_type = getattr(sym, "type", None)
        if not isinstance(sym_type, ps.PackedArrayType):
            return None
        fixed_range = getattr(sym_type, "fixedRange", None)
        elem_type = getattr(sym_type, "elementType", None)
        left = getattr(fixed_range, "left", None) if fixed_range is not None else None
        right = getattr(fixed_range, "right", None) if fixed_range is not None else None
        width = getattr(fixed_range, "width", None) if fixed_range is not None else None
        elem_width = getattr(elem_type, "bitWidth", None) if elem_type is not None else None
        if not isinstance(left, int):
            return None
        if not isinstance(right, int):
            return None
        if not isinstance(width, int):
            return None
        if not isinstance(elem_width, int):
            return None
        pos = idx - right if left >= right else right - idx
        if pos < 0 or pos >= width:
            return None
        return (pos, elem_width)

    def _select_index_range(self, sym: ps.Symbol, idx: int) -> Optional[tuple[int, int]]:
        pos_info = self._packed_outer_index_pos(sym, idx)
        if pos_info is None:
            sym_type = getattr(sym, "type", None)
            if not isinstance(sym_type, ps.PackedArrayType):
                return (idx, idx)
            return None
        pos, elem_width = pos_info
        low = pos * elem_width
        high = low + elem_width - 1
        return (low, high)

    def _select_range_for_indices(
        self, sym: ps.Symbol, left_idx: int, right_idx: int
    ) -> Optional[tuple[int, int]]:
        pos_left = self._packed_outer_index_pos(sym, left_idx)
        pos_right = self._packed_outer_index_pos(sym, right_idx)
        if pos_left is None or pos_right is None:
            sym_type = getattr(sym, "type", None)
            if not isinstance(sym_type, ps.PackedArrayType):
                low, high = sorted((left_idx, right_idx))
                return (low, high)
            return None
        left_pos, elem_width = pos_left
        right_pos, elem_width_right = pos_right
        if elem_width != elem_width_right:
            return None
        low_pos, high_pos = sorted((left_pos, right_pos))
        low = low_pos * elem_width
        high = (high_pos + 1) * elem_width - 1
        return (low, high)

    def _expr_name(self, expr: Optional[ps.Expression]) -> str:
        if expr is None:
            return "_unknown_var"
        if isinstance(expr, ps.ElementSelectExpression):
            base = self._expr_name(expr.value)
            _idx, idx_str = self._expr_index_and_str(expr.selector)
            return f"{base}[{idx_str}]"
        if isinstance(expr, ps.RangeSelectExpression):
            base = self._expr_name(expr.value)
            _left_idx, left_str = self._expr_index_and_str(expr.left)
            _right_idx, right_str = self._expr_index_and_str(expr.right)
            return self._range_select_name(base, left_str, right_str, expr.selectionKind)
        if self._is_member_access(expr):
            base = getattr(expr, "value", None)
            if isinstance(base, ps.Expression):
                return self._expr_name(base)
        sym = self._expr_symbol(expr)
        if sym is not None:
            return sym.name
        return str(expr.syntax) if expr.syntax else "_unknown_var"

    def _symbol_bit_width(self, sym: ps.Symbol) -> Optional[int]:
        sym_type = getattr(sym, "type", None)
        if sym_type is None:
            return None
        try:
            width = sym_type.bitWidth
        except Exception:
            return None
        return width if isinstance(width, int) else None

    def _expr_bit_width(self, expr: ps.Expression) -> Optional[int]:
        expr_type = getattr(expr, "type", None)
        if expr_type is None:
            return None
        try:
            width = expr_type.bitWidth
        except Exception:
            return None
        return width if isinstance(width, int) else None

    def _is_singleton_array_symbol(self, sym: ps.Symbol) -> bool:
        sym_type = getattr(sym, "type", None)
        if not isinstance(sym_type, ps.PackedArrayType):
            return False
        fixed_range = getattr(sym_type, "fixedRange", None)
        width = getattr(fixed_range, "width", None)
        return width == 1

    def _iter_expr_children(self, node: ps.Expression) -> Iterator[ps.Expression]:
        for attr in (
            "left",
            "right",
            "operand",
            "value",
            "selector",
            "arguments",
            "operands",
            "conditions",
        ):
            try:
                child = getattr(node, attr)
            except Exception:
                continue
            if isinstance(child, ps.Expression):
                yield child
            elif isinstance(child, (list, tuple)):
                for elem in child:
                    if isinstance(elem, ps.Expression):
                        yield elem
                    elif hasattr(elem, "expr"):
                        expr = elem.expr
                        if isinstance(expr, ps.Expression):
                            yield expr

    def _expr_used_inputs(
        self, expr: Optional[ps.Expression]
    ) -> tuple[list[tuple[ps.Symbol, Optional[tuple[int, int]]]], list[ElaboratableValue]]:
        syms: set[tuple[ps.Symbol, Optional[tuple[int, int]]]] = set()
        consts: list[ElaboratableValue] = []
        visited: set[int] = set()

        def _walk(node: Optional[ps.Expression]) -> None:
            if node is None:
                return
            node_id = id(node)
            if node_id in visited:
                return
            visited.add(node_id)
            const = self._expr_constant(node)
            if const is not None:
                consts.append(const)
                return
            if isinstance(node, ps.ElementSelectExpression):
                value_sym = getattr(node.value, "symbol", None) or self._expr_symbol(node.value)
                if value_sym is not None:
                    idx, _ = self._expr_index_and_str(node.selector)
                    rng = self._select_index_range(value_sym, idx) if idx is not None else None
                    syms.add((value_sym, rng))
                return
            if isinstance(node, ps.RangeSelectExpression):
                value_sym = getattr(node.value, "symbol", None) or self._expr_symbol(node.value)
                if value_sym is not None:
                    left_idx, _ = self._expr_index_and_str(node.left)
                    right_idx, _ = self._expr_index_and_str(node.right)
                    rng = None
                    if left_idx is not None and right_idx is not None:
                        rng = self._select_range_for_indices(value_sym, left_idx, right_idx)
                    syms.add((value_sym, rng))
                return
            if self._is_member_access(node):
                base = getattr(node, "value", None)
                base_sym = None
                if isinstance(base, ps.Expression):
                    base_sym = self._expr_symbol(base)
                else:
                    base_sym = getattr(base, "symbol", None)
                if base_sym is not None:
                    syms.add((base_sym, None))
                    return
                if isinstance(base, ps.Expression):
                    _walk(base)
                    return
            sym = getattr(node, "symbol", None)
            if sym is not None:
                base_sym = self._base_symbol_from_syntax(node)
                if base_sym is not None:
                    syms.add((base_sym, None))
                    return
                syms.add((sym, None))
                return
            for child in self._iter_expr_children(node):
                _walk(child)

        _walk(expr)
        return (list(syms), consts)

    def _timing_trigger_exprs(self, ctrl: Optional[Any]) -> list[ps.Expression]:
        if ctrl is None:
            return []
        exprs: list[ps.Expression] = []
        if isinstance(ctrl, ps.Expression):
            exprs.append(ctrl)
        for attr in ("expr", "expression", "condition"):
            val = getattr(ctrl, attr, None)
            if isinstance(val, ps.Expression):
                exprs.append(val)
        for attr in ("event", "events"):
            val = getattr(ctrl, attr, None)
            if val is None:
                continue
            if isinstance(val, (list, tuple)):
                for ev in val:
                    exprs.extend(self._timing_trigger_exprs(ev))
            else:
                exprs.extend(self._timing_trigger_exprs(val))
        return exprs

    def _bb_port_name_from_ref(self, ref: ReferencedPort) -> str:
        if ref.instance is None:
            return f"top.{ref.io.name}"
        if ref.instance.module in self.parser._select_modules.values():
            return ref.io.name
        return f"{ref.instance.name}.{ref.io.name}"

    def _bb_get_port(self, name: str, direction: PortDirection) -> Port:
        existing = self.bb_ports.get(name)
        if existing is not None:
            if existing.direction != direction:
                existing.direction = PortDirection.INOUT
            return existing
        port = Port(name=name, direction=direction)
        self.bb_mod.add_port(port)
        self.bb_ports[name] = port
        return port

    def _blackbox_instance(self) -> Optional[ModuleInstance]:
        if self.logic_inst is not None:
            return self.logic_inst
        self.logic_inst = ModuleInstance(name="(control)", module=self.bb_mod)
        self.components.append(self.logic_inst)
        return self.logic_inst

    def _route_through_blackbox(
        self, sources: Iterable[Union[ReferencedPort, ElaboratableValue]], sink: ReferencedPort
    ) -> None:
        src_list = list(sources)
        const_sources = [s for s in src_list if isinstance(s, ElaboratableValue)]
        port_sources = [s for s in src_list if isinstance(s, ReferencedPort)]
        if not port_sources:
            if len(const_sources) == 1:
                self.connections.append(ConstantConnection(source=const_sources[0], target=sink))
            return
        inst = self._blackbox_instance()
        if inst is None:
            return
        bb_out_name = self._bb_port_name_from_ref(sink)
        bb_out_port = self._bb_get_port(bb_out_name, PortDirection.OUT)
        bb_out_ref = ReferencedPort(instance=inst, io=bb_out_port)
        for src in port_sources:
            bb_in_name = self._bb_port_name_from_ref(src)
            bb_in_port = self._bb_get_port(bb_in_name, PortDirection.IN)
            bb_in_ref = ReferencedPort(instance=inst, io=bb_in_port)
            self.connections.append(PortConnection(source=src, target=bb_in_ref))
        sink_has_symbolic_dims = has_symbolic_dimensions(getattr(sink.io, "type", None))
        bb_out_dims = getattr(getattr(bb_out_ref.io, "type", None), "dimensions", None) or []
        if sink.instance is None and sink_has_symbolic_dims and (len(bb_out_dims) == 0):
            return
        self.connections.append(PortConnection(source=bb_out_ref, target=sink))

    def _merge_blackbox_concat_operands(
        self, items: list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]
    ) -> list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]:
        merged: list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]] = []
        run_sources: list[Union[ReferencedPort, ElaboratableValue]] = []
        run_active = False

        def _dedup_sources(
            sources: list[Union[ReferencedPort, ElaboratableValue]],
        ) -> list[Union[ReferencedPort, ElaboratableValue]]:
            seen: set[tuple[str, int, int, str]] = set()
            out: list[Union[ReferencedPort, ElaboratableValue]] = []
            for src in sources:
                if isinstance(src, ElaboratableValue):
                    key = ("const", 0, 0, str(src))
                else:
                    key = ("port", id(src.instance), id(src.io), repr(src.select))
                if key in seen:
                    continue
                seen.add(key)
                out.append(src)
            return out

        def _flush_run() -> None:
            nonlocal run_sources, run_active
            if not run_active:
                return
            merged.append((_dedup_sources(run_sources), True))
            run_sources = []
            run_active = False

        for sources, through_logic in items:
            if through_logic:
                if not run_active:
                    run_active = True
                    run_sources = []
                run_sources.extend(sources)
                continue
            _flush_run()
            merged.append((sources, through_logic))
        _flush_run()
        return merged

    def _create_concat(
        self, operands: list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]
    ) -> Optional[ReferencedPort]:
        operands = self._merge_blackbox_concat_operands(operands)
        concat_mod = self._get_concat_module(len(operands))
        taken = {c.name for c in self.components}
        name = f"concat_{self.concat_idx}"
        self.concat_idx += 1
        while name in taken:
            name = f"concat_{self.concat_idx}"
            self.concat_idx += 1
        inst = ModuleInstance(name=name, module=concat_mod)
        self.components.append(inst)
        out_port = concat_mod.ports.find_by_name("out")
        if out_port is None:
            return None
        out_ref = ReferencedPort(instance=inst, io=out_port)
        for idx, (op_sources, through_logic) in enumerate(operands):
            in_port = concat_mod.ports.find_by_name(f"in{idx}")
            if in_port is None:
                continue
            sink = ReferencedPort(instance=inst, io=in_port)
            if through_logic:
                self._route_through_blackbox(op_sources, sink)
            else:
                self._connect(op_sources, sink)
        return out_ref

    def _create_select(
        self,
        select_name: str,
        value_sources: list[Union[ReferencedPort, ElaboratableValue]],
        through_logic: bool,
    ) -> Optional[ReferencedPort]:
        if select_name in self._select_cache:
            return self._select_cache[select_name]
        select_mod = self._get_select_module(select_name)
        inst = ModuleInstance(name=select_name, module=select_mod)
        self.components.append(inst)
        out_port = select_mod.ports.find_by_name(select_name)
        if out_port is None:
            return None
        out_ref = ReferencedPort(instance=inst, io=out_port)
        self._select_cache[select_name] = out_ref
        var_name = select_name.split("[")[0]
        in_port = select_mod.ports.find_by_name(var_name)
        if in_port is not None:
            sink = ReferencedPort(instance=inst, io=in_port)
            if through_logic:
                self._route_through_blackbox(value_sources, sink)
            else:
                self._connect(value_sources, sink)
        return out_ref

    def _select_output(
        self,
        select_name: str,
        value_sources: list[Union[ReferencedPort, ElaboratableValue]],
        through_logic: bool,
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        select_out = self._create_select(select_name, value_sources, through_logic)
        return ([select_out], False) if select_out is not None else ([], False)

    def _external_input_port(self, sym: ps.Symbol) -> Optional[Port]:
        port = self.sym_ports.get(sym)
        if port is None:
            name = getattr(sym, "name", None)
            if isinstance(name, str):
                port_sym = self.ports_by_name.get(name)
                if port_sym is not None:
                    port = self.sym_ports.get(port_sym)
        if port is not None and port.direction in (PortDirection.IN, PortDirection.INOUT):
            return port
        return None

    def _range_select_name(
        self, var_name: str, left_str: str, right_str: str, selection_kind: ps.RangeSelectionKind
    ) -> str:
        if selection_kind == ps.RangeSelectionKind.IndexedUp:
            return f"{var_name}[{left_str}+:{right_str}]"
        if selection_kind == ps.RangeSelectionKind.IndexedDown:
            return f"{var_name}[{left_str}-:{right_str}]"
        return f"{var_name}[{left_str}:{right_str}]"

    def _select_span(self, op: ps.Expression) -> Optional[dict[str, Any]]:
        if isinstance(op, ps.ElementSelectExpression):
            if isinstance(op.value, (ps.ElementSelectExpression, ps.RangeSelectExpression)):
                return None
            base_sym = self._expr_symbol(op.value)
            if base_sym is None:
                return None
            idx, idx_str = self._expr_index_and_str(op.selector)
            if idx is None:
                return None
            return {
                "expr": op,
                "base": base_sym,
                "start": idx,
                "end": idx,
                "left_str": idx_str,
                "right_str": idx_str,
                "dir": 0,
            }
        if isinstance(op, ps.RangeSelectExpression):
            if op.selectionKind != ps.RangeSelectionKind.Simple:
                return None
            if isinstance(op.value, (ps.ElementSelectExpression, ps.RangeSelectExpression)):
                return None
            base_sym = self._expr_symbol(op.value)
            if base_sym is None:
                return None
            left_idx, left_str = self._expr_index_and_str(op.left)
            right_idx, right_str = self._expr_index_and_str(op.right)
            if left_idx is None or right_idx is None:
                return None
            if left_idx < right_idx:
                direction = 1
            elif left_idx > right_idx:
                direction = -1
            else:
                direction = 0
            return {
                "expr": op,
                "base": base_sym,
                "start": left_idx,
                "end": right_idx,
                "left_str": left_str,
                "right_str": right_str,
                "dir": direction,
            }
        return None

    def _flush_concat_run(
        self,
        run: "_ConcatRun",
        merged: list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]],
    ) -> None:
        if not run.items:
            return
        if len(run.items) == 1:
            merged.append(self._expr_sources_with_logic(run.items[0]["expr"]))
            run.reset()
            return
        first = run.items[0]
        last = run.items[-1]
        base_sym = run.base
        if base_sym is None:
            for span in run.items:
                merged.append(self._expr_sources_with_logic(span["expr"]))
            run.reset()
            return
        select_name = self._range_select_name(
            base_sym.name, first["left_str"], last["right_str"], ps.RangeSelectionKind.Simple
        )
        sources, through_logic = self._resolve_sources_with_logic(base_sym)
        merged.append(self._select_output(select_name, sources, through_logic))
        run.reset()

    def _concat_operand_sources(
        self, expr: ps.ConcatenationExpression
    ) -> list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]:
        merged: list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]] = []
        run = self._ConcatRun()
        for op in expr.operands:
            span = self._select_span(op)
            if span is None:
                self._flush_concat_run(run, merged)
                merged.append(self._expr_sources_with_logic(op))
                continue
            if not run.add(span):
                self._flush_concat_run(run, merged)
                run.add(span)
        self._flush_concat_run(run, merged)
        return merged

    def _covers_bit_driver(
        self, rng: Any, selector_idx: int, sel_range: Optional[tuple[int, int]], packed_value: bool
    ) -> bool:
        if rng is None:
            return True
        if not (isinstance(rng, tuple) and len(rng) == 2):
            return False
        low, high = sorted(rng)
        if sel_range is not None:
            sel_low, sel_high = sel_range
            return low <= sel_low and high >= sel_high
        if packed_value:
            return False
        return low <= selector_idx <= high

    def _covers_range_driver(
        self,
        rng: Any,
        sel_range: Optional[tuple[int, int]],
        packed_value: bool,
        left_idx: int,
        right_idx: int,
    ) -> bool:
        if rng is None:
            return True
        if not (isinstance(rng, tuple) and len(rng) == 2):
            return False
        drv_low, drv_high = sorted(rng)
        if sel_range is not None:
            sel_low, sel_high = sel_range
            return drv_low <= sel_low and drv_high >= sel_high
        if packed_value:
            return False
        sel_low, sel_high = sorted((left_idx, right_idx))
        return drv_low <= sel_low and drv_high >= sel_high

    def _expr_sources_concat(
        self, expr: ps.ConcatenationExpression
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        operand_sources = self._concat_operand_sources(expr)
        if len(operand_sources) == 1:
            return operand_sources[0]
        if operand_sources and all((through for _srcs, through in operand_sources)):
            sources: list[Union[ReferencedPort, ElaboratableValue]] = []
            for srcs, _through in operand_sources:
                sources.extend(srcs)
            return (sources, True)
        concat_out = self._create_concat(operand_sources)
        return ([concat_out], False) if concat_out is not None else ([], False)

    def _try_internal_bit_driver(
        self,
        value_sym: ps.Symbol,
        selector_idx: int,
        sel_range: Optional[tuple[int, int]],
        packed_value: bool,
    ) -> tuple[Optional[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]], bool]:
        """
        Returns:
          - (sources, through_logic) if we found a covering internal driver
          with concrete sources
          - None if we found no concrete sources
          - needs_logic=True if we encountered at least one logic-only covering driver
        """
        needs_logic = False
        for drv, rng in self.am.getDrivers(value_sym):
            cont = drv.containingSymbol
            if isinstance(cont, ps.InstanceBodySymbol):
                continue
            if not self._covers_bit_driver(rng, selector_idx, sel_range, packed_value):
                continue
            sources, through_logic = self._driver_sources_with_logic(drv, value_sym)
            if sources:
                return ((sources, through_logic), needs_logic)
            if through_logic:
                needs_logic = True
        return (None, needs_logic)

    def _expr_sources_bit_select(
        self, expr: ps.ElementSelectExpression
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        value_expr = expr.value
        selector_idx, selector_str = self._expr_index_and_str(expr.selector)
        value_sym = self._expr_symbol(value_expr)
        if value_sym is not None and self._is_singleton_array_symbol(value_sym):
            return self._expr_sources_with_logic(value_expr)
        if value_sym is not None and self._symbol_bit_width(value_sym) == 1:
            return self._expr_sources_with_logic(value_expr)
        var_name = self._expr_name(value_expr)
        needs_logic = False
        if value_sym is not None:
            packed_value = isinstance(getattr(value_sym, "type", None), ps.PackedArrayType)
            sel_range = (
                self._select_index_range(value_sym, selector_idx)
                if selector_idx is not None
                else None
            )
            if selector_idx is not None:
                found, add_logic = self._try_internal_bit_driver(
                    value_sym=value_sym,
                    selector_idx=selector_idx,
                    sel_range=sel_range,
                    packed_value=packed_value,
                )
                needs_logic = needs_logic or add_logic
                if found is not None:
                    sources, through_logic = found
                    return (sources, through_logic)
            ext_port = self._external_input_port(value_sym)
            if ext_port is not None:
                select_name = f"{var_name}[{selector_str}]"
                return self._select_output(select_name, [ReferencedPort.external(ext_port)], False)
            base_sources, base_logic = self._resolve_sources_with_logic(value_sym)
            if base_sources or base_logic:
                select_name = f"{var_name}[{selector_str}]"
                return self._select_output(select_name, base_sources, base_logic or needs_logic)
        select_name = f"{var_name}[{selector_str}]"
        return self._select_output(select_name, [], needs_logic)

    def _try_internal_range_driver(
        self,
        value_sym: ps.Symbol,
        packed_value: bool,
        sel_range: Optional[tuple[int, int]],
        left_idx: int,
        right_idx: int,
    ) -> tuple[Optional[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]], bool]:
        needs_logic = False
        for drv, rng in self.am.getDrivers(value_sym):
            cont = drv.containingSymbol
            if isinstance(cont, ps.InstanceBodySymbol):
                continue
            if not self._covers_range_driver(rng, sel_range, packed_value, left_idx, right_idx):
                continue
            sources, through_logic = self._driver_sources_with_logic(drv, value_sym)
            if sources:
                return ((sources, through_logic), needs_logic)
            if through_logic:
                needs_logic = True
        return (None, needs_logic)

    def _expr_sources_range_select(
        self, expr: ps.RangeSelectExpression
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        value_expr = expr.value
        selection_kind = expr.selectionKind
        left_idx, left_str = self._expr_index_and_str(expr.left)
        right_idx, right_str = self._expr_index_and_str(expr.right)
        value_sym = self._expr_symbol(value_expr)
        if value_sym is not None and self._is_singleton_array_symbol(value_sym):
            return self._expr_sources_with_logic(value_expr)
        if value_sym is not None and self._symbol_bit_width(value_sym) == 1:
            return self._expr_sources_with_logic(value_expr)
        var_name = self._expr_name(value_expr)
        needs_logic = False
        if value_sym is not None:
            packed_value = isinstance(getattr(value_sym, "type", None), ps.PackedArrayType)
            sel_range = (
                self._select_range_for_indices(value_sym, left_idx, right_idx)
                if left_idx is not None and right_idx is not None
                else None
            )
            if (
                selection_kind == ps.RangeSelectionKind.Simple
                and left_idx is not None
                and (right_idx is not None)
            ):
                found, add_logic = self._try_internal_range_driver(
                    value_sym=value_sym,
                    packed_value=packed_value,
                    sel_range=sel_range,
                    left_idx=left_idx,
                    right_idx=right_idx,
                )
                needs_logic = needs_logic or add_logic
                if found is not None:
                    sources, through_logic = found
                    return (sources, through_logic)
            ext_port = self._external_input_port(value_sym)
            if ext_port is not None:
                select_name = self._range_select_name(var_name, left_str, right_str, selection_kind)
                return self._select_output(select_name, [ReferencedPort.external(ext_port)], False)
            base_sources, base_logic = self._resolve_sources_with_logic(value_sym)
            if base_sources or base_logic:
                select_name = self._range_select_name(var_name, left_str, right_str, selection_kind)
                return self._select_output(select_name, base_sources, base_logic or needs_logic)
        select_name = self._range_select_name(var_name, left_str, right_str, selection_kind)
        return self._select_output(select_name, [], needs_logic)

    def _expr_sources_generic(
        self, expr: ps.Expression
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        const_val = self._expr_constant(expr)
        if const_val is not None:
            return ([const_val], False)
        sym = getattr(expr, "symbol", None)
        if sym is not None:
            return self._resolve_sources_with_logic(sym)
        used_syms, used_consts = self._expr_used_inputs(expr)
        sources: list[Union[ReferencedPort, ElaboratableValue]] = [*used_consts]
        seen: set[tuple[str, int, int, str]] = {("const", 0, 0, str(c)) for c in used_consts}
        for usym, urange in used_syms:
            srcs, _ = self._resolve_sources_with_logic(usym, urange)
            for src in srcs:
                key = (
                    ("const", 0, 0, str(src))
                    if isinstance(src, ElaboratableValue)
                    else ("port", id(src.instance), id(src.io), repr(src.select))
                )
                if key in seen:
                    continue
                seen.add(key)
                sources.append(src)
        return (sources, True)

    def _strip_outer_parens(self, text: str) -> str:
        out = text.strip()
        while out.startswith("(") and out.endswith(")"):
            depth = 0
            balanced = True
            for i, ch in enumerate(out):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth < 0 or (depth == 0 and i != len(out) - 1):
                        balanced = False
                        break
            if not balanced or depth != 0:
                break
            out = out[1:-1].strip()
        return out

    def _resolve_text_base_sources(
        self, name: str
    ) -> Optional[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]:
        sym = self._lookup_symbol_by_name(name)
        if sym is not None:
            return self._resolve_sources_with_logic(sym)
        refs = list(self.name_to_instance_ports.get(name, []))
        if refs:
            ref_sources: list[Union[ReferencedPort, ElaboratableValue]] = [*refs]
            return (ref_sources, False)
        return None

    def _parse_text_select(
        self, sel: str
    ) -> tuple[str, Optional[str], Optional[ps.RangeSelectionKind]]:
        if "+:" in sel:
            left, right = sel.split("+:", 1)
            return (left.strip(), right.strip(), ps.RangeSelectionKind.IndexedUp)
        if "-:" in sel:
            left, right = sel.split("-:", 1)
            return (left.strip(), right.strip(), ps.RangeSelectionKind.IndexedDown)
        if ":" in sel:
            left, right = sel.split(":", 1)
            return (left.strip(), right.strip(), ps.RangeSelectionKind.Simple)
        return (sel.strip(), None, None)

    def _apply_text_selects(
        self,
        base_name: str,
        sources: list[Union[ReferencedPort, ElaboratableValue]],
        through_logic: bool,
        selects_txt: str,
    ) -> Optional[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]:
        if selects_txt.strip() == "":
            return (sources, through_logic)
        cur_sources: list[Union[ReferencedPort, ElaboratableValue]] = [*sources]
        cur_logic = through_logic
        cur_base = base_name
        for sel_txt in re.findall("\\[([^\\]]+)\\]", selects_txt):
            left, right, selection_kind = self._parse_text_select(sel_txt.strip())
            if left == "":
                return None
            if right is None:
                select_name = f"{cur_base}[{left}]"
            else:
                if selection_kind is None:
                    return None
                select_name = self._range_select_name(cur_base, left, right, selection_kind)
            select_out = self._create_select(select_name, cur_sources, cur_logic)
            if select_out is None:
                return None
            next_sources: list[Union[ReferencedPort, ElaboratableValue]] = [select_out]
            cur_sources, cur_logic, cur_base = (next_sources, False, select_name)
        return (cur_sources, cur_logic)

    def _sources_from_text_expr(
        self, text: str
    ) -> Optional[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]:
        txt = self._strip_outer_parens(text)
        if txt == "":
            return None
        if (ident_name := self._expr_identifier_name(txt)) is not None:
            return self._resolve_text_base_sources(ident_name)
        escaped_match = re.fullmatch("\\\\(?P<base>\\S+)(?P<selects>(?:\\s*\\[[^\\]]+\\])*)", txt)
        if escaped_match is not None:
            base = escaped_match.group("base")
            resolved = self._resolve_text_base_sources(base)
            if resolved is None:
                return None
            return self._apply_text_selects(
                base, resolved[0], resolved[1], escaped_match.group("selects")
            )
        plain_match = re.fullmatch(
            "(?P<base>[A-Za-z_$][A-Za-z0-9_$]*)(?P<selects>(?:\\[[^\\]]+\\])*)", txt
        )
        if plain_match is None:
            return None
        base = plain_match.group("base")
        resolved = self._resolve_text_base_sources(base)
        if resolved is None:
            return None
        return self._apply_text_selects(
            base, resolved[0], resolved[1], plain_match.group("selects")
        )

    def _source_text_from_range(self, rng: Any) -> str:
        if rng is None:
            return ""
        try:
            src = self.parser.src_man.getSourceText(rng.start.buffer)
            return src[rng.start.offset : rng.end.offset].strip()
        except Exception:
            return ""

    def _recover_from_text_candidates(
        self, *candidates: Optional[str]
    ) -> Optional[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]:
        for cand in candidates:
            txt = (cand or "").strip()
            if txt == "":
                continue
            recovered = self._sources_from_text_expr(txt)
            if recovered is not None:
                return recovered
        return None

    def _norm_named_token(self, name: str) -> str:
        out = name.strip()
        return out[1:].strip() if out.startswith("\\") else out

    def _named_expr_sources(
        self,
        expr: ps.NamedValueExpression,
        inst_sym: Optional[ps.InstanceSymbol],
        port_name: Optional[str],
    ) -> Optional[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]]:
        named_sym = getattr(expr, "symbol", None)
        named_syntax = getattr(expr, "syntax", None)
        if named_syntax is not None and str(named_syntax).strip() not in {"", "None"}:
            return None
        raw_expr = None
        if inst_sym is not None and port_name is not None:
            raw_expr = self._raw_instance_port_expr(inst_sym, port_name)
            if raw_expr is not None and raw_expr.strip() == "":
                return ([], False)
            recovered = self._recover_from_text_candidates(raw_expr)
            if recovered is not None:
                return recovered
            pname = self._norm_named_token(port_name)
            if re.fullmatch("[A-Za-z_$][A-Za-z0-9_$]*", pname):
                if named_sym is not None:
                    sym_name = getattr(named_sym, "name", None)
                    if isinstance(sym_name, str) and self._norm_named_token(sym_name) == pname:
                        return self._resolve_sources_with_logic(named_sym)
                    pname_sym = self._lookup_symbol_by_name(pname)
                    if pname_sym is not None:
                        pname_sources, pname_logic = self._resolve_sources_with_logic(pname_sym)
                        if pname_sources:
                            return (pname_sources, pname_logic)
                else:
                    recovered = self._sources_from_text_expr(pname)
                    if recovered is not None:
                        return recovered
        if named_sym is not None:
            return None
        recovered = self._recover_from_text_candidates(
            self._source_text_from_range(getattr(expr, "sourceRange", None))
        )
        return recovered if recovered is not None else ([], False)

    def _invalid_expr_sources(
        self, expr: ps.Expression, inst_sym: Optional[ps.InstanceSymbol], port_name: Optional[str]
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        rng = getattr(expr, "sourceRange", None)
        from_range = ""
        if rng is not None and getattr(rng.start, "offset", 0) != getattr(rng.end, "offset", 0):
            from_range = self._source_text_from_range(rng)
        from_inst = (
            self._raw_instance_port_expr(inst_sym, port_name) if inst_sym and port_name else ""
        )
        txt = from_range or (from_inst or "").strip()
        if txt != "" and is_simple_sv_literal(txt):
            return ([ElaboratableValue(txt)], False)
        recovered = self._recover_from_text_candidates(txt)
        return recovered if recovered is not None else ([], False)

    def _expr_sources_with_logic(
        self,
        expr: Optional[ps.Expression],
        inst_sym: Optional[ps.InstanceSymbol] = None,
        port_name: Optional[str] = None,
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        if expr is None:
            return ([], False)
        invalid_expr_t = getattr(ps, "InvalidExpression", None)
        if invalid_expr_t is not None and isinstance(expr, invalid_expr_t):
            return self._invalid_expr_sources(expr, inst_sym, port_name)
        if isinstance(expr, ps.AssignmentExpression):
            left = getattr(expr, "left", None)
            right = getattr(expr, "right", None)
            empty_arg_t = getattr(ps, "EmptyArgumentExpression", None)
            if left is not None and (
                right is None or (empty_arg_t is not None and isinstance(right, empty_arg_t))
            ):
                return self._expr_sources_with_logic(left)
        if isinstance(expr, ps.ConversionExpression):
            operand = getattr(expr, "operand", None)
            if isinstance(operand, ps.Expression):
                return self._expr_sources_with_logic(operand)
        if isinstance(expr, ps.ConcatenationExpression):
            return self._expr_sources_concat(expr)
        if isinstance(expr, ps.ElementSelectExpression):
            return self._expr_sources_bit_select(expr)
        if isinstance(expr, ps.RangeSelectExpression):
            return self._expr_sources_range_select(expr)
        if isinstance(expr, ps.NamedValueExpression):
            recovered_named = self._named_expr_sources(expr, inst_sym, port_name)
            if recovered_named is not None:
                return recovered_named
        syntax_txt = str(getattr(expr, "syntax", "")).strip()
        raw_txt = (
            (self._raw_instance_port_expr(inst_sym, port_name) or "").strip()
            if syntax_txt == "" and inst_sym and port_name
            else None
        )
        recovered = self._recover_from_text_candidates(syntax_txt, raw_txt)
        if recovered is not None:
            return recovered
        return self._expr_sources_generic(expr)

    def _instance_port_sources(
        self, sym: ps.Symbol, inst_sym: Optional[ps.InstanceSymbol] = None
    ) -> list[Union[ReferencedPort, ElaboratableValue]]:
        def _as_sources(
            refs: list[ReferencedPort],
        ) -> list[Union[ReferencedPort, ElaboratableValue]]:
            return [*refs]

        if inst_sym is None:
            refs = list(self.sym_to_instance_ports.get(sym, []))
            if refs:
                return _as_sources(refs)
            sym_name = getattr(sym, "name", None)
            if isinstance(sym_name, str):
                refs = list(self.name_to_instance_ports.get(sym_name, []))
                if refs:
                    return _as_sources(refs)
                return _as_sources(self._instance_output_sources_by_name(sym_name))
            return []
        inst = self.instance_map.get(inst_sym)
        if inst is None:
            return []
        outputs = self.instance_output_sources.get(inst_sym, [])
        refs = [
            ReferencedPort(instance=inst, io=port)
            for expr_sym, port in outputs
            if expr_sym is sym or expr_sym == sym
        ]
        if refs:
            return _as_sources(refs)
        sym_name = getattr(sym, "name", None)
        if isinstance(sym_name, str):
            refs_by_name = [
                ref for ref in self.name_to_instance_ports.get(sym_name, []) if ref.instance is inst
            ]
            if refs_by_name:
                return _as_sources(refs_by_name)
            recovered: list[ReferencedPort] = []
            for child_port in inst.module.ports:
                if child_port.direction not in (PortDirection.OUT, PortDirection.INOUT):
                    continue
                expr_txt = (self._raw_instance_port_expr(inst_sym, child_port.name) or "").strip()
                expr_name = self._expr_identifier_name(expr_txt)
                if expr_name == sym_name:
                    recovered.append(ReferencedPort(instance=inst, io=child_port))
            return _as_sources(recovered)
        return []

    def _build_instance_output_sources_by_name_cache(self) -> dict[str, list[ReferencedPort]]:
        by_name: dict[str, list[ReferencedPort]] = {}
        for inst_sym, inst in self.instance_map.items():
            child_mod = inst.module
            for pc in self.inst_port_conns.get(inst_sym, []):
                child_port = child_mod.ports.find_by_name(pc.port.name)
                if child_port is None:
                    continue
                if child_port.direction not in (PortDirection.OUT, PortDirection.INOUT):
                    continue
                ref = ReferencedPort(instance=inst, io=child_port)
                expr_sym_name: Optional[str] = None
                expr_sym = self._expr_symbol(pc.expression)
                if expr_sym is not None:
                    expr_sym_name = getattr(expr_sym, "name", None)
                    if isinstance(expr_sym_name, str):
                        by_name.setdefault(expr_sym_name, []).append(ref)
                    else:
                        expr_sym_name = None
                expr_txt = str(getattr(pc.expression, "syntax", "")).strip()
                if expr_txt == "":
                    expr_txt = self._source_text_from_range(
                        getattr(pc.expression, "sourceRange", None)
                    )
                if expr_txt == "":
                    expr_txt = (self._raw_instance_port_expr(inst_sym, pc.port.name) or "").strip()
                expr_name = self._expr_identifier_name(expr_txt)
                if expr_name is not None and expr_name != expr_sym_name:
                    by_name.setdefault(expr_name, []).append(ref)
        return by_name

    def _instance_output_sources_by_name(self, name: str) -> list[ReferencedPort]:
        if self._instance_output_sources_by_name_cache is None:
            self._instance_output_sources_by_name_cache = (
                self._build_instance_output_sources_by_name_cache()
            )
        return list(self._instance_output_sources_by_name_cache.get(name, []))

    def _is_unpacked_array_symbol(self, sym: ps.Symbol) -> bool:
        if not isinstance(sym, (ps.VariableSymbol, ps.NetSymbol)):
            return False
        sym_type = sym.type
        if isinstance(sym_type, ps.FixedSizeUnpackedArrayType):
            return True
        if not isinstance(sym_type, ps.PackedArrayType):
            return False
        elem_type = getattr(sym_type, "elementType", None)
        scalar_type = getattr(ps, "ScalarType", None)
        if scalar_type is not None and isinstance(elem_type, scalar_type):
            return False
        fixed_range = getattr(sym_type, "fixedRange", None)
        width = getattr(fixed_range, "width", None)
        return width not in (None, 1)

    def _is_comb_block(self, block: ps.ProceduralBlockSymbol) -> bool:
        if block.procedureKind == ps.ProceduralBlockKind.AlwaysComb:
            return True
        if block.procedureKind != ps.ProceduralBlockKind.Always:
            return False
        timing = getattr(block.body, "timing", None)
        return timing is None or getattr(timing, "kind", None) == ps.TimingControlKind.ImplicitEvent

    def _stmt_from_node(self, node: Any) -> Optional[ps.Statement]:
        if isinstance(node, ps.Statement):
            return node
        for attr in ("stmt", "statement", "body"):
            stmt = getattr(node, attr, None)
            if isinstance(stmt, ps.Statement):
                return stmt
        return None

    def _exprs_from_stmt(self, node: Any) -> list[ps.Expression]:
        exprs: list[ps.Expression] = []
        for attr in ("predicate", "condition", "expr", "expression", "cond"):
            expr = getattr(node, attr, None)
            if isinstance(expr, ps.Expression):
                exprs.append(expr)
        conditions = getattr(node, "conditions", None)
        if isinstance(conditions, list):
            for cond in conditions:
                expr = getattr(cond, "expr", None)
                if isinstance(expr, ps.Expression):
                    exprs.append(expr)
        return exprs

    def _case_items(self, node: Any) -> list[Any]:
        items = (
            getattr(node, "items", None)
            or getattr(node, "itemList", None)
            or getattr(node, "caseItems", None)
        )
        items_list = getattr(items, "list", None)
        if isinstance(items_list, list):
            return items_list
        return items if isinstance(items, list) else []

    def _lhs_matches_sym(self, sym: ps.Symbol, lhs: ps.Expression) -> bool:
        lhs_sym = self._expr_symbol(lhs) or getattr(lhs, "symbol", None)
        if lhs_sym is sym:
            return True
        lhs_name = getattr(lhs_sym, "name", None)
        sym_name = getattr(sym, "name", None)
        return isinstance(lhs_name, str) and lhs_name == sym_name

    def _stmt_assigns_sym(self, stmt: Optional[ps.Statement], sym: ps.Symbol) -> bool:
        if stmt is None:
            return False
        checker = self._STMT_ASSIGN_CHECKERS.get(type(stmt))
        if checker is not None:
            return checker(stmt, sym)
        inner = getattr(stmt, "stmt", None)
        if isinstance(inner, ps.Statement):
            return self._stmt_assigns_sym(inner, sym)
        for child in self._iter_stmt_children(stmt):
            if self._stmt_assigns_sym(child, sym):
                return True
        return False

    def _assign_expr_stmt(self, stmt: ps.Statement, sym: ps.Symbol) -> bool:
        node = cast(ps.ExpressionStatement, stmt)
        expr = node.expr
        if not isinstance(expr, ps.AssignmentExpression):
            return False
        return self._lhs_matches_sym(sym, expr.left)

    def _assign_block_stmt(self, stmt: ps.Statement, sym: ps.Symbol) -> bool:
        node = cast(ps.BlockStatement, stmt)
        return self._stmt_assigns_sym(self._stmt_from_node(node.body), sym)

    def _assign_stmt_list(self, stmt: ps.Statement, sym: ps.Symbol) -> bool:
        node = cast(ps.StatementList, stmt)
        return any((self._stmt_assigns_sym(s, sym) for s in node.list))

    def _assign_conditional(self, stmt: ps.Statement, sym: ps.Symbol) -> bool:
        node = cast(ps.ConditionalStatement, stmt)
        then_stmt = self._stmt_from_node(getattr(node, "ifTrue", None)) or self._stmt_from_node(
            getattr(node, "statement", None)
        )
        else_stmt = self._stmt_from_node(getattr(node, "ifFalse", None)) or self._stmt_from_node(
            getattr(node, "elseClause", None)
        )
        return self._stmt_assigns_sym(then_stmt, sym) or self._stmt_assigns_sym(else_stmt, sym)

    def _assign_case(self, stmt: ps.Statement, sym: ps.Symbol) -> bool:
        node = cast(ps.CaseStatement, stmt)
        return any(
            (
                self._stmt_assigns_sym(self._stmt_from_node(item), sym)
                for item in self._case_items(node)
            )
        )

    def _assign_false(self, _stmt: ps.Statement, _sym: ps.Symbol) -> bool:
        return False

    def _procedural_conditional_sources(
        self, stmt: Optional[ps.Statement], sym: ps.Symbol
    ) -> list[Union[ReferencedPort, ElaboratableValue]]:
        if stmt is None:
            return []
        out: list[Union[ReferencedPort, ElaboratableValue]] = []
        stack: list[Any] = [stmt]
        while stack:
            node = stack.pop()
            if isinstance(node, ps.ConditionalStatement):
                then_stmt = self._stmt_from_node(
                    getattr(node, "ifTrue", None)
                ) or self._stmt_from_node(getattr(node, "statement", None))
                else_stmt = self._stmt_from_node(
                    getattr(node, "ifFalse", None)
                ) or self._stmt_from_node(getattr(node, "elseClause", None))
                if self._stmt_assigns_sym(then_stmt, sym) or self._stmt_assigns_sym(else_stmt, sym):
                    for cond_expr in self._exprs_from_stmt(node):
                        srcs, _ = self._expr_sources_with_logic(cond_expr)
                        out.extend(srcs)
            elif isinstance(node, ps.CaseStatement):
                if any(
                    (
                        self._stmt_assigns_sym(self._stmt_from_node(item), sym)
                        for item in self._case_items(node)
                    )
                ):
                    for cond_expr in self._exprs_from_stmt(node):
                        srcs, _ = self._expr_sources_with_logic(cond_expr)
                        out.extend(srcs)
            inner = getattr(node, "stmt", None)
            if isinstance(inner, ps.Statement):
                stack.append(inner)
            for attr in ("body", "ifTrue", "ifFalse", "elseClause"):
                child = getattr(node, attr, None)
                child_stmt = self._stmt_from_node(child)
                if child_stmt is not None:
                    stack.append(child_stmt)
            for attr in ("list", "statements"):
                child = getattr(node, attr, None)
                if isinstance(child, list):
                    stack.extend([c for c in child if isinstance(c, ps.Statement)])
                else:
                    child_list = getattr(child, "list", None)
                    if isinstance(child_list, list):
                        stack.extend([c for c in child_list if isinstance(c, ps.Statement)])
        return out

    def _procedural_seq_sources(
        self, block: ps.ProceduralBlockSymbol, sym: ps.Symbol
    ) -> list[Union[ReferencedPort, ElaboratableValue]]:
        timing = getattr(block.body, "timing", None)
        trigger_sources: list[Union[ReferencedPort, ElaboratableValue]] = []
        seen_triggers: set[int] = set()
        for expr in self._timing_trigger_exprs(timing):
            expr_id = id(expr)
            if expr_id in seen_triggers:
                continue
            seen_triggers.add(expr_id)
            srcs, _ = self._expr_sources_with_logic(expr)
            trigger_sources.extend(srcs)
        trigger_sources.extend(self._procedural_conditional_sources(block.body, sym))
        return trigger_sources

    def _comb_collect_assignment(
        self, state: "_CombState", sym: ps.Symbol, expr: ps.Expression
    ) -> None:
        if not isinstance(expr, ps.AssignmentExpression):
            return
        if not self._lhs_matches_sym(sym, expr.left):
            return
        rhs_sources, rhs_logic = self._expr_sources_with_logic(expr.right)
        state.sources.extend(rhs_sources)
        state.proc_logic = state.proc_logic or rhs_logic
        state.assignments += 1

    def _comb_handle_conditional(
        self, state: "_CombState", sym: ps.Symbol, node: ps.ConditionalStatement
    ) -> None:
        then_stmt = self._stmt_from_node(getattr(node, "ifTrue", None)) or self._stmt_from_node(
            getattr(node, "statement", None)
        )
        else_stmt = self._stmt_from_node(getattr(node, "ifFalse", None)) or self._stmt_from_node(
            getattr(node, "elseClause", None)
        )
        if self._stmt_assigns_sym(then_stmt, sym) or self._stmt_assigns_sym(else_stmt, sym):
            for cond_expr in self._exprs_from_stmt(node):
                cond_sources, _ = self._expr_sources_with_logic(cond_expr)
                state.sources.extend(cond_sources)
            state.proc_logic = True

    def _comb_handle_case(
        self, state: "_CombState", sym: ps.Symbol, node: ps.CaseStatement
    ) -> None:
        if any(
            (
                self._stmt_assigns_sym(self._stmt_from_node(item), sym)
                for item in self._case_items(node)
            )
        ):
            for cond_expr in self._exprs_from_stmt(node):
                cond_sources, _ = self._expr_sources_with_logic(cond_expr)
                state.sources.extend(cond_sources)
            state.proc_logic = True

    def _procedural_comb_sources(
        self, block: ps.ProceduralBlockSymbol, sym: ps.Symbol
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        state = self._CombState()
        stack: list[Any] = [block.body]
        while stack:
            stmt = stack.pop()
            if stmt is None:
                continue
            if isinstance(stmt, ps.ExpressionStatement):
                self._comb_collect_assignment(state, sym, cast(ps.ExpressionStatement, stmt).expr)
            elif isinstance(stmt, ps.BlockStatement):
                stack.append(self._stmt_from_node(cast(ps.BlockStatement, stmt).body))
            elif isinstance(stmt, ps.StatementList):
                stack.extend(reversed(cast(ps.StatementList, stmt).list))
            elif isinstance(stmt, ps.ConditionalStatement):
                self._comb_handle_conditional(state, sym, cast(ps.ConditionalStatement, stmt))
                node = cast(ps.ConditionalStatement, stmt)
                stack.append(
                    self._stmt_from_node(getattr(node, "ifFalse", None))
                    or self._stmt_from_node(getattr(node, "elseClause", None))
                )
                stack.append(
                    self._stmt_from_node(getattr(node, "ifTrue", None))
                    or self._stmt_from_node(getattr(node, "statement", None))
                )
            elif isinstance(stmt, ps.CaseStatement):
                self._comb_handle_case(state, sym, cast(ps.CaseStatement, stmt))
                node = cast(ps.CaseStatement, stmt)
                for item in reversed(self._case_items(node)):
                    stack.append(self._stmt_from_node(item))
            else:
                inner = getattr(stmt, "stmt", None)
                if isinstance(inner, ps.Statement):
                    stack.append(inner)
        return (state.sources, state.proc_logic or state.assignments > 1)

    def _driver_sources_with_logic(
        self, drv: ps.ValueDriver, sym: ps.Symbol
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        cont = drv.containingSymbol
        if isinstance(cont, ps.ContinuousAssignSymbol):
            assignment = cont.assignment
            rhs = (
                assignment.right if isinstance(assignment, ps.AssignmentExpression) else assignment
            )
            return self._expr_sources_with_logic(rhs)
        if isinstance(cont, ps.InstanceSymbol):
            return (self._instance_port_sources(sym, cont), False)
        if isinstance(cont, ps.InstanceBodySymbol):
            ext_port = self.sym_ports.get(sym)
            return (
                ([ReferencedPort.external(ext_port)], False)
                if ext_port is not None
                else ([], False)
            )
        if isinstance(cont, ps.ProceduralBlockSymbol):
            if self._is_comb_block(cont):
                return self._procedural_comb_sources(cont, sym)
            return (self._procedural_seq_sources(cont, sym), True)
        logger.debug("Unhandled driver container for %s: %s", sym, cont)
        return ([], False)

    def _combine_disjoint_drivers(
        self,
        sym: ps.Symbol,
        drivers: list[tuple[ps.ValueDriver, tuple[int, int]]],
        driver_sources: dict[
            ps.ValueDriver, tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]
        ],
    ) -> Optional[list[Union[ReferencedPort, ElaboratableValue]]]:
        if self._symbol_bit_width(sym) == 1:
            return None
        allow_single = len(drivers) == 1 and self._is_unpacked_array_symbol(sym)
        if allow_single:
            drv = drivers[0][0]
            drv_sources = driver_sources.get(drv)
            if drv_sources is None:
                return None
            sources, through_logic = drv_sources
            if len(sources) == 1 and (not through_logic):
                return sources
            concat_out = self._create_concat([drv_sources])
            return [concat_out] if concat_out is not None else None
        if len(drivers) <= 1:
            return None
        ranges: list[tuple[int, int, ps.ValueDriver]] = []
        for drv, rng in drivers:
            if not isinstance(rng, tuple) or len(rng) != 2:
                return None
            if not all((isinstance(x, int) for x in rng)):
                return None
            low, high = sorted(rng)
            ranges.append((low, high, drv))
        ranges.sort(key=lambda r: r[0])
        non_overlapping = [ranges[0]]
        for (_, prev_high, prev_drv), (cur_low, cur_high, cur_drv) in zip(ranges, ranges[1:]):
            if cur_low <= prev_high:
                logger.error(
                    "Overlapping driver ranges for range [%d:%d] of %s: {%s}, {%s}",
                    prev_high,
                    cur_low,
                    sym,
                    prev_drv.containingSymbol.syntax,
                    cur_drv.containingSymbol.syntax,
                )
                continue
            non_overlapping.append((cur_low, cur_high, cur_drv))
        if len(non_overlapping) <= 1:
            return None
        ordered = sorted(non_overlapping, key=lambda r: r[1], reverse=True)
        operand_sources: list[tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]] = []
        for _, _, drv in ordered:
            drv_sources = driver_sources.get(drv)
            if drv_sources is None:
                return None
            operand_sources.append(drv_sources)
        concat_out = self._create_concat(operand_sources)
        if concat_out is None:
            return None
        return [concat_out]

    def _normalize_range(self, rng: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
        if rng is None:
            return None
        low, high = sorted(rng)
        return (low, high)

    def _cache_sources(
        self,
        key: tuple[str, Optional[tuple[int, int]]],
        sources: list[Union[ReferencedPort, ElaboratableValue]],
        logic: bool,
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        self._resolve_cache[key] = (sources[:], logic)
        return (sources, logic)

    def _iter_stmt_children(self, stmt: ps.Statement) -> Iterator[ps.Statement]:
        for attr in ("stmt", "body", "ifTrue", "ifFalse", "elseClause"):
            child = getattr(stmt, attr, None)
            if isinstance(child, ps.Statement):
                yield child
        for attr in ("list", "statements"):
            child = getattr(stmt, attr, None)
            if isinstance(child, list):
                for entry in child:
                    if isinstance(entry, ps.Statement):
                        yield entry
            else:
                child_list = getattr(child, "list", None)
                if isinstance(child_list, list):
                    for entry in child_list:
                        if isinstance(entry, ps.Statement):
                            yield entry

    def _symbol_cache_key(self, sym: Optional[ps.Symbol]) -> str:
        if sym is None:
            return "<none>"
        lex_path = getattr(sym, "lexicalPath", None)
        if lex_path:
            return str(lex_path)
        name = getattr(sym, "name", None)
        if name is not None:
            return str(name)
        return repr(sym)

    def _resolve_no_driver_sources(
        self, sym: ps.Symbol, logic_only_driver: bool
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        cont_exprs = self.cont_assign_map.get(sym)
        if cont_exprs:
            if len(cont_exprs) > 1:
                logger.warning(
                    "Multiple continuous assignments detected for %s; selecting a single source",
                    getattr(sym, "name", sym),
                )
            return self._expr_sources_with_logic(cont_exprs[0])
        cont_texts = self.cont_assign_text_map.get(sym)
        if cont_texts:
            if len(cont_texts) > 1:
                logger.warning(
                    "Multiple textual continuous assignments detected for %s; "
                    "selecting a single source",
                    getattr(sym, "name", sym),
                )
            rhs_txt = cont_texts[0].strip()
            if is_simple_sv_literal(rhs_txt):
                return ([ElaboratableValue(rhs_txt)], False)
            rhs_name = rhs_txt
            if rhs_name.startswith("\\"):
                rhs_name = rhs_name[1:].strip()
            if re.fullmatch("[A-Za-z_$][A-Za-z0-9_$]*", rhs_name):
                rhs_sym = self._lookup_symbol_by_name(rhs_name)
                if rhs_sym is not None:
                    return self._resolve_sources_with_logic(rhs_sym)
        inst_sources = self._instance_port_sources(sym)
        ext_port = self._external_input_port(sym)
        if ext_port is not None:
            return ([ReferencedPort.external(ext_port)], False)
        if inst_sources:
            return (inst_sources, False)
        sym_name = getattr(sym, "name", None)
        if sym_name in self.procedural_assignments:
            sources: list[Union[ReferencedPort, ElaboratableValue]] = []
            for expr in self.procedural_assignments[sym_name]:
                expr_sources, _logic = self._expr_sources_with_logic(expr)
                sources.extend(expr_sources)
            return (sources, True)
        return ([], logic_only_driver)

    def _collect_driver_candidates(
        self, sym: ps.Symbol, rng: Optional[tuple[int, int]]
    ) -> tuple[
        list[tuple[ps.ValueDriver, tuple[int, int]]],
        dict[ps.ValueDriver, tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]],
        bool,
    ]:
        filtered_drivers: list[tuple[ps.ValueDriver, tuple[int, int]]] = []
        driver_sources: dict[
            ps.ValueDriver, tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]
        ] = {}
        logic_only_driver = False
        for drv, drv_rng in self.am.getDrivers(sym):
            if rng is not None and isinstance(drv_rng, tuple) and (len(drv_rng) == 2):
                if all((isinstance(x, int) for x in drv_rng)):
                    drv_low, drv_high = sorted(drv_rng)
                    if drv_high < rng[0] or drv_low > rng[1]:
                        continue
            sources, drv_logic = self._driver_sources_with_logic(drv, sym)
            if not sources:
                logic_only_driver = logic_only_driver or drv_logic
                continue
            filtered_drivers.append((drv, drv_rng))
            driver_sources[drv] = (sources, drv_logic)
        return (filtered_drivers, driver_sources, logic_only_driver)

    def _resolve_sources_impl(
        self, sym: ps.Symbol, rng: Optional[tuple[int, int]]
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        filtered_drivers, driver_sources, logic_only_driver = self._collect_driver_candidates(
            sym, rng
        )
        combined = self._combine_disjoint_drivers(sym, filtered_drivers, driver_sources)
        if combined is not None:
            return (combined, logic_only_driver)
        if not filtered_drivers:
            return self._resolve_no_driver_sources(sym, logic_only_driver)
        sources: list[Union[ReferencedPort, ElaboratableValue]] = []
        logic = len(filtered_drivers) > 1 or logic_only_driver
        for drv, _ in filtered_drivers:
            srcs, drv_logic = driver_sources.get(drv, ([], False))
            sources.extend(srcs)
            logic = logic or drv_logic
        return (sources, logic)

    def _resolve_sources_with_logic(
        self, sym: Optional[ps.Symbol] = None, rng: Optional[tuple[int, int]] = None
    ) -> tuple[list[Union[ReferencedPort, ElaboratableValue]], bool]:
        if sym is None:
            return ([], False)
        rng = self._normalize_range(rng)
        key = (self._symbol_cache_key(sym), rng)
        cached = self._resolve_cache.get(key)
        if cached is not None:
            return (cached[0][:], cached[1])
        if key in self._resolving:
            if key not in self._cycle_reported:
                logger.warning(
                    "Circular dependency detected for symbol: %s%s",
                    self._symbol_cache_key(sym),
                    f"[{rng[0]}:{rng[1]}]" if rng is not None else "",
                )
                self._cycle_reported.add(key)
            return ([], False)
        self._resolving.add(key)
        try:
            sources, logic = self._resolve_sources_impl(sym, rng)
            return self._cache_sources(key, sources, logic)
        finally:
            self._resolving.discard(key)

    def _connect(
        self, sources: Iterable[Union[ReferencedPort, ElaboratableValue]], sink: ReferencedPort
    ):
        src_list = list(sources)
        if not src_list:
            return
        if len(src_list) > 1:
            logger.warning(
                "Multiple drivers detected for %s; selecting a single source",
                getattr(sink.io, "name", sink.io),
            )

        def _pick_key(
            src: Union[ReferencedPort, ElaboratableValue],
        ) -> tuple[int, int, int, str, str, str]:
            if isinstance(src, ElaboratableValue):
                return (-1, -1, -1, "", "", str(src))
            dir_rank = {PortDirection.OUT: 2, PortDirection.INOUT: 1, PortDirection.IN: 0}.get(
                src.io.direction, 0
            )
            logic_rank = 0 if src.instance is self.logic_inst else 1
            scope_rank = 0 if src.instance is None else 1
            inst_name = src.instance.name if src.instance is not None else ""
            return (dir_rank, logic_rank, scope_rank, inst_name, src.io.name, repr(src.select))

        picked: Union[ReferencedPort, ElaboratableValue]
        picked = max(src_list, key=_pick_key)
        if sink.instance is not None and sink.io.direction in (
            PortDirection.IN,
            PortDirection.INOUT,
        ):
            ext_same_name = [
                src
                for src in src_list
                if isinstance(src, ReferencedPort)
                and src.instance is None
                and (src.io.direction in (PortDirection.IN, PortDirection.INOUT))
                and (src.io.name == sink.io.name)
            ]
            if len(ext_same_name) == 1:
                picked = ext_same_name[0]
        if isinstance(picked, ReferencedPort):
            src_dims = getattr(getattr(picked.io, "type", None), "dimensions", None) or []
            sink_has_symbolic_dims = has_symbolic_dimensions(getattr(sink.io, "type", None))
            if (
                picked.instance is self.logic_inst
                and sink.instance is None
                and sink_has_symbolic_dims
                and (len(src_dims) == 0)
            ):
                return
        if isinstance(picked, ElaboratableValue):
            self.connections.append(ConstantConnection(source=picked, target=sink))
        else:
            self.connections.append(PortConnection(source=picked, target=sink))

    def _flattened_output_ref(self, name: str) -> Optional[ReferencedPort]:
        for inst in self.components:
            prefix = f"{inst.name}__"
            if not name.startswith(prefix):
                continue
            port_name = name[len(prefix) :]
            if port_name == "":
                continue
            port = inst.module.ports.find_by_name(port_name)
            if port is None or port.direction not in (PortDirection.OUT, PortDirection.INOUT):
                continue
            return ReferencedPort(instance=inst, io=port)
        return None

    def _instance_port_expr_text(
        self,
        inst_sym: ps.InstanceSymbol,
        port_name: str,
        pc_by_name: Optional[dict[str, ps.PortConnection]] = None,
    ) -> str:
        expr_txt = ""
        if pc_by_name is None:
            for pc in self.inst_port_conns.get(inst_sym, []):
                if pc.port.name != port_name:
                    continue
                expr_txt = str(getattr(pc.expression, "syntax", "")).strip()
                if expr_txt == "":
                    expr_txt = self._source_text_from_range(
                        getattr(pc.expression, "sourceRange", None)
                    )
                break
        else:
            pc = pc_by_name.get(port_name)
            if pc is not None:
                expr_txt = str(getattr(pc.expression, "syntax", "")).strip()
                if expr_txt == "":
                    expr_txt = self._source_text_from_range(
                        getattr(pc.expression, "sourceRange", None)
                    )
        if expr_txt == "":
            expr_txt = (self._raw_instance_port_expr(inst_sym, port_name) or "").strip()
        return expr_txt[1:].strip() if expr_txt.startswith("\\") else expr_txt

    def _external_output_ports(self) -> dict[str, Port]:
        return {
            p.name: p
            for p in self.mod.ports
            if p.direction in (PortDirection.OUT, PortDirection.INOUT)
        }

    def _connect_external_output_name(
        self,
        source: ReferencedPort,
        ext_name: str,
        ext_out_ports: dict[str, Port],
        connected_ext: set[str],
    ) -> bool:
        if ext_name in connected_ext:
            return False
        ext_port = ext_out_ports.get(ext_name)
        if ext_port is None:
            return False
        self.connections.append(
            PortConnection(source=source, target=ReferencedPort.external(ext_port))
        )
        connected_ext.add(ext_name)
        return True

    def _count_instance_output_names(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for inst in self.components:
            for p in inst.module.ports:
                if p.direction not in (PortDirection.OUT, PortDirection.INOUT):
                    continue
                counts[p.name] = counts.get(p.name, 0) + 1
        return counts

    def _connected_external_names(self, ext_out_ports: dict[str, Port]) -> set[str]:
        connected: set[str] = set()
        for conn in self.connections:
            tgt = getattr(conn, "target", None)
            if (
                isinstance(tgt, ReferencedPort)
                and tgt.instance is None
                and (tgt.io.name in ext_out_ports)
            ):
                connected.add(tgt.io.name)
        return connected

    def _repair_instance_text_external_outputs(
        self,
        ext_out_ports: dict[str, Port],
        connected_ext: set[str],
        instance_output_name_counts: dict[str, int],
    ) -> None:
        for inst_sym, inst in self.instance_map.items():
            pc_by_name = {pc.port.name: pc for pc in self.inst_port_conns.get(inst_sym, [])}
            for child_port in inst.module.ports:
                if child_port.direction not in (PortDirection.OUT, PortDirection.INOUT):
                    continue
                source = ReferencedPort(instance=inst, io=child_port)
                expr_txt = self._instance_port_expr_text(inst_sym, child_port.name, pc_by_name)
                expr_name = self._expr_identifier_name(expr_txt)
                if expr_name is not None:
                    self._connect_external_output_name(
                        source, expr_name, ext_out_ports, connected_ext
                    )
                    continue
                if instance_output_name_counts.get(child_port.name, 0) == 1:
                    self._connect_external_output_name(
                        source, child_port.name, ext_out_ports, connected_ext
                    )

    def _repair_unique_same_name_dangling(
        self, ext_out_ports: dict[str, Port], connected_ext: set[str]
    ) -> None:
        dangling = [name for name in ext_out_ports if name not in connected_ext]
        for out_name in dangling:
            candidates: list[ReferencedPort] = []
            for inst in self.components:
                for p in inst.module.ports:
                    if (
                        p.direction in (PortDirection.OUT, PortDirection.INOUT)
                        and p.name == out_name
                    ):
                        candidates.append(ReferencedPort(instance=inst, io=p))
            if len(candidates) != 1:
                continue
            self._connect_external_output_name(
                candidates[0], out_name, ext_out_ports, connected_ext
            )

    def _repair_last_resort_single_dangling(
        self, ext_out_ports: dict[str, Port], connected_ext: set[str]
    ) -> None:
        dangling = [name for name in ext_out_ports if name not in connected_ext]
        if len(dangling) != 1:
            return
        unbound_outputs: list[ReferencedPort] = []
        for inst in self.components:
            for p in inst.module.ports:
                if p.direction not in (PortDirection.OUT, PortDirection.INOUT):
                    continue
                has_conn = any(
                    (
                        isinstance(c, PortConnection)
                        and isinstance(c.source, ReferencedPort)
                        and (c.source.instance is inst)
                        and (c.source.io.name == p.name)
                        for c in self.connections
                    )
                )
                if not has_conn:
                    unbound_outputs.append(ReferencedPort(instance=inst, io=p))
        if len(unbound_outputs) == 1:
            self._connect_external_output_name(
                unbound_outputs[0], dangling[0], ext_out_ports, connected_ext
            )

    def _repair_external_output_connections_from_instance_text(self) -> None:
        ext_out_ports = self._external_output_ports()
        if not ext_out_ports:
            return
        connected_ext = self._connected_external_names(ext_out_ports)
        instance_output_name_counts = self._count_instance_output_names()
        self._repair_instance_text_external_outputs(
            ext_out_ports, connected_ext, instance_output_name_counts
        )
        self._repair_unique_same_name_dangling(ext_out_ports, connected_ext)
        self._repair_last_resort_single_dangling(ext_out_ports, connected_ext)

    def _repair_dangling_external_outputs_from_raw_instance_text(self) -> None:
        ext_out_ports = {
            p.name: p
            for p in self.mod.ports
            if p.direction in (PortDirection.OUT, PortDirection.INOUT)
        }
        if not ext_out_ports:
            return
        connected_ext = {
            c.target.io.name
            for c in self.connections
            if isinstance(c, PortConnection)
            and isinstance(c.target, ReferencedPort)
            and (c.target.instance is None)
        }
        dangling_ext = {name for name in ext_out_ports if name not in connected_ext}
        if not dangling_ext:
            return
        candidates_by_out: dict[str, list[ReferencedPort]] = {name: [] for name in dangling_ext}
        for inst_sym, inst in self.instance_map.items():
            for child_port in inst.module.ports:
                if child_port.direction not in (PortDirection.OUT, PortDirection.INOUT):
                    continue
                has_conn = any(
                    (
                        isinstance(c, PortConnection)
                        and isinstance(c.source, ReferencedPort)
                        and (c.source.instance is inst)
                        and (c.source.io.name == child_port.name)
                        for c in self.connections
                    )
                )
                if has_conn:
                    continue
                expr_txt = (self._raw_instance_port_expr(inst_sym, child_port.name) or "").strip()
                if expr_txt.startswith("\\"):
                    expr_txt = expr_txt[1:].strip()
                if not re.fullmatch("[A-Za-z_$][A-Za-z0-9_$]*", expr_txt):
                    continue
                if expr_txt not in candidates_by_out:
                    continue
                candidates_by_out[expr_txt].append(ReferencedPort(instance=inst, io=child_port))
        for out_name in list(dangling_ext):
            cands = candidates_by_out.get(out_name, [])
            if len(cands) != 1:
                continue
            self.connections.append(
                PortConnection(
                    source=cands[0], target=ReferencedPort.external(ext_out_ports[out_name])
                )
            )

    def _strip_blackbox_only_concats(self) -> None:
        if self.logic_inst is None:
            return
        concat_mods = set(self.parser._concat_modules.values())
        concat_insts = [inst for inst in self.components if inst.module in concat_mods]
        if not concat_insts:
            return
        concat_set = set(concat_insts)

        def _conn_instances(
            conn: Connection,
        ) -> tuple[Optional[ModuleInstance], Optional[ModuleInstance]]:
            src_inst = getattr(getattr(conn, "source", None), "instance", None)
            tgt_inst = getattr(getattr(conn, "target", None), "instance", None)
            return (src_inst, tgt_inst)

        inst_state: dict[ModuleInstance, list[bool]] = {
            inst: [False, True] for inst in concat_insts
        }
        for conn in self.connections:
            src_inst, tgt_inst = _conn_instances(conn)
            if src_inst in concat_set:
                state = inst_state[src_inst]
                state[0] = True
                if tgt_inst is not self.logic_inst:
                    state[1] = False
            if tgt_inst in concat_set:
                state = inst_state[tgt_inst]
                state[0] = True
                if src_inst is not self.logic_inst:
                    state[1] = False
        remove_insts: set[ModuleInstance] = {
            inst for inst, (has_conn, ok) in inst_state.items() if has_conn and ok
        }
        if not remove_insts:
            return
        self.connections[:] = [
            conn
            for conn in self.connections
            if _conn_instances(conn)[0] not in remove_insts
            and _conn_instances(conn)[1] not in remove_insts
        ]
        self.components[:] = [inst for inst in self.components if inst not in remove_insts]
        bb_used: set[int] = set()
        for conn in self.connections:
            src_inst, tgt_inst = _conn_instances(conn)
            if (
                src_inst is self.logic_inst
                and isinstance(conn, PortConnection)
                and isinstance(conn.source, ReferencedPort)
            ):
                bb_used.add(id(conn.source.io))
            if (
                tgt_inst is self.logic_inst
                and isinstance(conn, PortConnection)
                and isinstance(conn.target, ReferencedPort)
            ):
                bb_used.add(id(conn.target.io))
        self.bb_mod._ports[:] = [p for p in self.bb_mod._ports if id(p) in bb_used]
        self.bb_ports.clear()
        self.bb_ports.update({p.name: p for p in self.bb_mod._ports})

    def _repair_lonely_concat_output(self) -> None:
        if not self.components:
            return
        ext_out_ports = [
            p for p in self.mod.ports if p.direction in (PortDirection.OUT, PortDirection.INOUT)
        ]
        if not ext_out_ports:
            return
        connected_ext = {
            c.target.io.name
            for c in self.connections
            if isinstance(c, PortConnection)
            and isinstance(c.target, ReferencedPort)
            and (c.target.instance is None)
        }
        dangling_ext = [p for p in ext_out_ports if p.name not in connected_ext]
        if len(dangling_ext) != 1:
            return
        concat_out_refs: list[ReferencedPort] = []
        for inst in self.components:
            is_concat = inst.module.id.name.startswith("concat_")
            if not is_concat:
                continue
            out_port = inst.module.ports.find_by_name("out")
            if out_port is None:
                continue
            ref = ReferencedPort(instance=inst, io=out_port)
            has_conn = any(
                (
                    isinstance(c, PortConnection)
                    and isinstance(c.source, ReferencedPort)
                    and (c.source.instance is inst)
                    and (c.source.io.name == "out")
                    for c in self.connections
                )
            )
            if not has_conn:
                concat_out_refs.append(ref)
        if len(concat_out_refs) != 1:
            return
        self.connections.append(
            PortConnection(
                source=concat_out_refs[0], target=ReferencedPort.external(dangling_ext[0])
            )
        )

    def _repair_dangling_external_outputs_from_concat_text(self) -> None:
        if not self.components:
            return
        ext_out_ports = {
            p.name: p
            for p in self.mod.ports
            if p.direction in (PortDirection.OUT, PortDirection.INOUT)
        }
        if not ext_out_ports:
            return
        connected_ext = {
            c.target.io.name
            for c in self.connections
            if isinstance(c, PortConnection)
            and isinstance(c.target, ReferencedPort)
            and (c.target.instance is None)
        }
        dangling_ext = {name for name in ext_out_ports if name not in connected_ext}
        if not dangling_ext:
            return
        instsym_by_inst = {inst: inst_sym for inst_sym, inst in self.instance_map.items()}

        def _is_concat(inst: ModuleInstance) -> bool:
            return inst.module.id.name.startswith("concat_")

        for inst in self.components:
            if not _is_concat(inst):
                continue
            out_port = inst.module.ports.find_by_name("out")
            if out_port is None:
                continue
            already_connected = any(
                (
                    isinstance(c, PortConnection)
                    and isinstance(c.source, ReferencedPort)
                    and (c.source.instance is inst)
                    and (c.source.io.name == "out")
                    for c in self.connections
                )
            )
            if already_connected:
                continue
            inst_sym = instsym_by_inst.get(inst)
            if inst_sym is None:
                continue
            expr_txt = (self._raw_instance_port_expr(inst_sym, "out") or "").strip()
            if expr_txt.startswith("\\"):
                expr_txt = expr_txt[1:].strip()
            if not re.fullmatch("[A-Za-z_$][A-Za-z0-9_$]*", expr_txt):
                continue
            if expr_txt not in dangling_ext:
                continue
            self.connections.append(
                PortConnection(
                    source=ReferencedPort(instance=inst, io=out_port),
                    target=ReferencedPort.external(ext_out_ports[expr_txt]),
                )
            )
            dangling_ext.remove(expr_txt)
            if not dangling_ext:
                break

    def _helper_control_instances(self) -> list[ModuleInstance]:
        helper_insts = [
            inst for inst in self.components if inst.module.id.name.endswith(".(control)")
        ]
        if self.logic_inst is not None:
            helper_insts.append(self.logic_inst)
        return helper_insts

    def _connected_helper_input_names(self, helper: ModuleInstance) -> set[str]:
        return {
            c.target.io.name
            for c in self.connections
            if isinstance(c, PortConnection)
            and isinstance(c.target, ReferencedPort)
            and (c.target.instance is helper)
        }

    def _split_helper_src_port(self, raw_name: str) -> Optional[tuple[str, str]]:
        name = raw_name.strip()
        if name.startswith("\\"):
            name = name[1:].strip()
        if "." not in name:
            return None
        inst_name, port_name = name.split(".", 1)
        return (inst_name, port_name)

    def _should_repair_helper_input(
        self, raw_expr: str, inst_name: str, port_name: str, src_inst_sym: ps.InstanceSymbol
    ) -> bool:
        implied_wire = f"{inst_name}__{port_name}"
        if raw_expr in {f"{inst_name}.{port_name}", implied_wire}:
            return True
        if raw_expr != "":
            return False
        src_expr = self._instance_port_expr_text(src_inst_sym, port_name)
        return bool(
            src_expr
            and re.fullmatch("[A-Za-z_$][A-Za-z0-9_$]*", src_expr)
            and (src_expr == implied_wire)
        )

    def _repair_single_helper_input(
        self,
        helper: ModuleInstance,
        helper_sym: ps.InstanceSymbol,
        helper_port: Port,
        inst_by_name: dict[str, ModuleInstance],
        instsym_by_inst: dict[ModuleInstance, ps.InstanceSymbol],
    ) -> bool:
        split = self._split_helper_src_port(helper_port.name)
        if split is None:
            return False
        inst_name, port_name = split
        src_inst = inst_by_name.get(inst_name)
        if src_inst is None:
            return False
        src_inst_sym = instsym_by_inst.get(src_inst)
        if src_inst_sym is None:
            return False
        raw_expr = (self._raw_instance_port_expr(helper_sym, helper_port.name) or "").strip()
        if raw_expr.startswith("\\"):
            raw_expr = raw_expr[1:].strip()
        if not self._should_repair_helper_input(raw_expr, inst_name, port_name, src_inst_sym):
            return False
        src_port = src_inst.module.ports.find_by_name(port_name)
        if src_port is None or src_port.direction not in (PortDirection.OUT, PortDirection.INOUT):
            return False
        self.connections.append(
            PortConnection(
                source=ReferencedPort(instance=src_inst, io=src_port),
                target=ReferencedPort(instance=helper, io=helper_port),
            )
        )
        return True

    def _repair_logic_inputs_from_instance_port_names(self) -> None:
        inst_by_name: dict[str, ModuleInstance] = {inst.name: inst for inst in self.components}
        instsym_by_inst = {inst: inst_sym for inst_sym, inst in self.instance_map.items()}
        helper_insts = self._helper_control_instances()
        if not helper_insts:
            return
        for helper in helper_insts:
            connected_helper_inputs = self._connected_helper_input_names(helper)
            helper_sym = instsym_by_inst.get(helper)
            if helper_sym is None:
                continue
            for helper_port in helper.module.ports:
                if helper_port.direction not in (PortDirection.IN, PortDirection.INOUT):
                    continue
                if helper_port.name in connected_helper_inputs:
                    continue
                if self._repair_single_helper_input(
                    helper, helper_sym, helper_port, inst_by_name, instsym_by_inst
                ):
                    connected_helper_inputs.add(helper_port.name)

    def _build_module_header(self) -> ps.InstanceBodySymbol:
        body: ps.InstanceBodySymbol = self.mod_ast.body
        mod_id = Identifier(name=body.name)
        self.mod = Module(id=mod_id)
        self.sym_ports: dict[ps.Symbol, Port] = {}
        for param_ast in body.parameters:
            param = self.parser._parse_parameter_ast(param_ast)
            if param is not None:
                self.mod.add_parameter(param)
        for port_ast in body.portList:
            if isinstance(port_ast, ps.InterfacePortSymbol):
                if port_ast.interfaceDef is None:
                    logger.warning(
                        "There is no interface definition in provided sources "
                        f"for interface '{port_ast.lexicalPath}'"
                    )
                    continue
                for conn in port_ast.connection:
                    if isinstance(conn, ps.InstanceSymbol):
                        self.parser._visit_instance_ast(conn, self.comp, True)
                name = port_ast.interfaceDef.name
                idef = self.parser._interfaces.get(name)
                if idef is None:
                    logger.warning(
                        "Could not resolve interface definition '%s' in '%s'. "
                        "Using an empty placeholder interface.",
                        name,
                        port_ast.lexicalPath,
                    )
                    idef = InterfaceDefinition(id=Identifier(name=name), signals=[])
                    self.parser._interfaces[name] = idef
                    self.parser._placeholder_interfaces.add(name)
                mode = self.parser._modport_names.get((name, port_ast.modport))
                if mode is None:
                    mode = InterfaceMode.UNSPECIFIED
                inst = Interface(
                    name=port_ast.name,
                    mode=mode,
                    definition=idef,
                    signals={s._id: None for s in idef.signals},
                )
                self.mod.add_interface(inst)
            else:
                if not isinstance(port_ast, ps.PortSymbol) or not isinstance(
                    port_ast.internalSymbol, (ps.VariableSymbol, ps.NetSymbol)
                ):
                    logger.error(
                        "Exotic port symbol: %s, %s",
                        port_ast,
                        getattr(port_ast, "internalSymbol", MISSING),
                    )
                    continue
                port = Port(
                    name=port_ast.name,
                    direction=_slang_dir_to_ir_dir(port_ast.direction),
                    type=self.parser._parse_var_type_ast(port_ast.internalSymbol),
                )
                self.mod.add_port(port)
                self.sym_ports[port_ast.internalSymbol] = port
        file = Path(self.parser.src_man.getFileName(body.location))
        line = self.parser.src_man.getLineNumber(body.location)
        column = self.parser.src_man.getColumnNumber(body.location)
        self.mod.add_reference(FileReference(file=file, line=line, column=column))
        return body

    def _init_parsing_state(self, body: ps.InstanceBodySymbol) -> None:
        self.components: list[ModuleInstance] = []
        self.connections: list[Union[PortConnection, ConstantConnection]] = []
        self.concat_idx = 0
        self.am = self.parser._ensure_analysis_manager(self.comp)
        self.instance_map: dict[ps.InstanceSymbol, ModuleInstance] = {}
        self.inst_port_conns: dict[ps.InstanceSymbol, list[ps.PortConnection]] = {}
        self.sym_by_name: dict[str, ps.Symbol] = {}
        self.sym_by_norm_name: dict[str, ps.Symbol] = {}
        self.ports_by_name: dict[str, ps.PortSymbol] = {}
        self.ports_by_norm_name: dict[str, ps.PortSymbol] = {}
        self._populate_symbol_lookup(body)
        self._collect_instances(body)
        self._member_expr_types = self._build_member_expr_types()
        self._collect_continuous_assignments(body)
        self._collect_procedural_assignments(body)
        self._prepare_instance_output_tracking(body)
        self._init_blackbox_state(body)
        self._init_resolution_state()

    def _populate_symbol_lookup(self, body: ps.InstanceBodySymbol) -> None:
        for sym in self.sym_ports:
            name = getattr(sym, "name", None)
            if not isinstance(name, str):
                continue
            self.sym_by_name[name] = sym
            self.sym_by_norm_name.setdefault(self._norm_sv_ident(name), sym)
            if isinstance(sym, ps.PortSymbol):
                self.ports_by_name[name] = sym
                self.ports_by_norm_name.setdefault(self._norm_sv_ident(name), sym)

        for entry in body:
            if not isinstance(entry, (ps.VariableSymbol, ps.NetSymbol)):
                continue
            self.sym_by_name[entry.name] = entry
            self.sym_by_norm_name.setdefault(self._norm_sv_ident(entry.name), entry)

    def _build_member_expr_types(self) -> tuple[type, ...]:
        return tuple(
            t
            for t in (
                getattr(ps, "MemberSelectExpression", None),
                getattr(ps, "MemberAccessExpression", None),
                getattr(ps, "MemberSelectExpressionSyntax", None),
                getattr(ps, "MemberAccessExpressionSyntax", None),
            )
            if t is not None
        )

    def _collect_continuous_assignments(self, body: ps.InstanceBodySymbol) -> None:
        self.cont_assign_map: dict[ps.Symbol, list[ps.Expression]] = {}
        self.cont_assign_text_map: dict[ps.Symbol, list[str]] = {}
        for entry in body:
            if not isinstance(entry, ps.ContinuousAssignSymbol):
                continue
            assignment = entry.assignment
            if isinstance(assignment, ps.AssignmentExpression):
                lhs = assignment.left
                rhs = assignment.right
            else:
                lhs = getattr(assignment, "left", None)
                rhs = getattr(assignment, "right", None)
            if rhs is None or not isinstance(lhs, ps.NamedValueExpression):
                raw = self._raw_source_for_node(assignment) or self._raw_source_for_node(entry)
                m = re.match(
                    "\\s*(?:assign\\s+)?(?P<lhs>\\\\\\S+|[A-Za-z_$][A-Za-z0-9_$]*)\\s*=\\s*(?P<rhs>.*?)\\s*;?\\s*$",
                    raw,
                    flags=re.S,
                )
                if m is None:
                    continue
                lhs_name = m.group("lhs").strip()
                if lhs_name.startswith("\\"):
                    lhs_name = lhs_name[1:]
                lhs_sym = self._lookup_symbol_by_name(lhs_name)
                if lhs_sym is None:
                    continue
                rhs_txt = m.group("rhs").strip()
                self.cont_assign_text_map.setdefault(lhs_sym, []).append(rhs_txt)
                continue
            lhs_sym = self._expr_symbol(lhs)
            if lhs_sym is None:
                continue
            self.cont_assign_map.setdefault(lhs_sym, []).append(rhs)

    def _collect_procedural_assignments(self, body: ps.InstanceBodySymbol) -> None:
        self.procedural_assignments: dict[str, list[ps.Expression]] = {}
        for entry in body:
            if isinstance(entry, ps.ProceduralBlockSymbol):
                self._walk_procedural_stmts(entry.body)

    def _prepare_instance_output_tracking(self, body: ps.InstanceBodySymbol) -> None:
        self.instance_output_sources: dict[ps.InstanceSymbol, list[tuple[ps.Symbol, Port]]] = {}
        self.sym_to_instance_ports: dict[ps.Symbol, list[ReferencedPort]] = {}
        self.name_to_instance_ports: dict[str, list[ReferencedPort]] = {}
        self._instance_port_expr_text_cache: dict[ps.InstanceSymbol, dict[str, str]] = {}
        self._module_text_for_port_scan = ""
        body_syn = getattr(body, "syntax", None)
        body_rng = getattr(body_syn, "sourceRange", None) if body_syn is not None else None
        if body_rng is not None:
            try:
                src = self.parser.src_man.getSourceText(body_rng.start.buffer)
                self._module_text_for_port_scan = src[body_rng.start.offset : body_rng.end.offset]
            except Exception:
                self._module_text_for_port_scan = ""
        self._port_expr_re = re.compile(
            "\\.\\s*(?P<name>\\\\\\S+|[A-Za-z_][A-Za-z0-9_$.]*)\\s*\\(\\s*(?P<expr>.*?)\\s*\\)",
            flags=re.S,
        )
        self._cache_instance_outputs()

    def _init_blackbox_state(self, body: ps.InstanceBodySymbol) -> None:
        self.logic_inst: Optional[ModuleInstance] = None
        bb_base_name = f"{body.name}.(control)"
        bb_name = bb_base_name
        bb_idx = 1
        while bb_name in self.parser._submodules:
            bb_name = f"{bb_base_name}_{bb_idx}"
            bb_idx += 1
        self.bb_mod = Module(id=Identifier(name=bb_name, vendor="topwrap", library="internal"))
        self.bb_ports: dict[str, Port] = {}
        self._select_cache: dict[str, ReferencedPort] = {}
        self._instance_output_sources_by_name_cache: Optional[dict[str, list[ReferencedPort]]] = (
            None
        )

    def _init_resolution_state(self) -> None:
        self._STMT_ASSIGN_CHECKERS: dict[type, Any] = {
            ps.ExpressionStatement: self._assign_expr_stmt,
            ps.BlockStatement: self._assign_block_stmt,
            ps.StatementList: self._assign_stmt_list,
            ps.ConditionalStatement: self._assign_conditional,
            ps.CaseStatement: self._assign_case,
            ps.ForLoopStatement: self._assign_false,
            ps.ForeachLoopStatement: self._assign_false,
            ps.VariableDeclStatement: self._assign_false,
        }
        self._resolving: set[tuple[str, Optional[tuple[int, int]]]] = set()
        self._resolve_cache: dict[
            tuple[str, Optional[tuple[int, int]]],
            tuple[list[Union[ReferencedPort, ElaboratableValue]], bool],
        ] = {}
        self._cycle_reported: set[tuple[str, Optional[tuple[int, int]]]] = set()

    def _recover_instance_input_sources(
        self, inst_sym: ps.InstanceSymbol, pc: ps.PortConnection
    ) -> list[Union[ReferencedPort, ElaboratableValue]]:
        raw_expr = str(getattr(pc.expression, "syntax", "")).strip()
        if raw_expr == "":
            rng = getattr(pc.expression, "sourceRange", None)
            if rng is not None:
                try:
                    src = self.parser.src_man.getSourceText(rng.start.buffer)
                    raw_expr = src[rng.start.offset : rng.end.offset].strip()
                except Exception:
                    raw_expr = ""
        if raw_expr == "":
            raw_expr = (self._raw_instance_port_expr(inst_sym, pc.port.name) or "").strip()

        expr_name = self._expr_identifier_name(raw_expr)
        if expr_name is None:
            return []

        srcs: list[Union[ReferencedPort, ElaboratableValue]] = list(
            self.name_to_instance_ports.get(expr_name, [])
        )
        if not srcs:
            srcs.extend(self._instance_output_sources_by_name(expr_name))
        if not srcs:
            flat_ref = self._flattened_output_ref(expr_name)
            if flat_ref is not None:
                srcs = [flat_ref]
        if srcs:
            return srcs

        expr_sym = self._lookup_symbol_by_name(expr_name)
        if expr_sym is None:
            return []
        ext_in = self._external_input_port(expr_sym)
        return [ReferencedPort.external(ext_in)] if ext_in is not None else []

    def _connect_component_inputs(self) -> None:
        for inst_sym, inst in self.instance_map.items():
            child_mod = inst.module
            for pc in self.inst_port_conns.get(inst_sym, []):
                child_port = child_mod.ports.find_by_name(pc.port.name)
                if child_port is None:
                    continue
                sink = ReferencedPort(instance=inst, io=child_port)
                if child_port.direction in (PortDirection.IN, PortDirection.INOUT):
                    srcs, through_logic = self._expr_sources_with_logic(
                        pc.expression, inst_sym, pc.port.name
                    )
                    if not srcs and (not through_logic):
                        srcs = self._recover_instance_input_sources(inst_sym, pc)
                    if not srcs and (not through_logic):
                        continue
                    if through_logic:
                        self._route_through_blackbox(srcs, sink)
                    else:
                        self._connect(srcs, sink)

    def _connect_external_outputs(self) -> None:
        for sym, port in self.sym_ports.items():
            if port.direction in (PortDirection.OUT, PortDirection.INOUT):
                sink = ReferencedPort.external(port)
                srcs, through_logic = self._resolve_sources_with_logic(sym)
                if not srcs:
                    sym_name = getattr(sym, "name", None)
                    if isinstance(sym_name, str):
                        srcs = list(self.name_to_instance_ports.get(sym_name, []))
                        if not srcs:
                            srcs = self._instance_output_sources_by_name(sym_name)
                if not srcs and (not through_logic):
                    continue
                if through_logic:
                    self._route_through_blackbox(srcs, sink)
                else:
                    self._connect(srcs, sink)

    def _finalize_module_design(self) -> Module:
        self._repair_external_output_connections_from_instance_text()
        self._repair_dangling_external_outputs_from_raw_instance_text()
        self._strip_blackbox_only_concats()
        self._repair_lonely_concat_output()
        self._repair_dangling_external_outputs_from_concat_text()
        self._repair_logic_inputs_from_instance_port_names()
        if self.components or self.connections:
            self.mod.design = Design(components=self.components, connections=self.connections)
        return self.mod

    def parse(self) -> Module:
        body = self._build_module_header()
        self._init_parsing_state(body)
        self._connect_component_inputs()
        self._connect_external_outputs()
        return self._finalize_module_design()


class SystemVerilogSlangParser:
    src_man: ps.SourceManager
    diag_log_level: ps.DiagnosticSeverity

    #: A dictionary of preloaded IR Modules whose instances
    #: can be encountered in the SV sources.
    #: Keyed by :py:meth:`_ir_id_to_sv_str`
    _modules: dict[str, Module]

    #: A dictionary of submodules encountered when parsing modules
    #: Keyed by :py:meth:`_ir_id_to_sv_str`
    _submodules: dict[str, Module]

    #: A dictionary of both preloaded and currently parsed interface
    #: definitions. If the name of an encountered SV interface
    #: matches any of the entries here then that interface is assumed
    #: Keyed by :py:meth:`_ir_id_to_sv_str`
    _interfaces: dict[str, InterfaceDefinition]

    #: A dictionary of only currently parsed modules keyed by their
    #: name in the sources.
    _parsed_mods: dict[str, Module]

    #: Custom type aliases defined by typedefs that can be used
    #: further down in the AST. Pre-parsed into IR Logic.
    _typedefs: dict[str, Logic]

    #: A dictionary mapping a modport in an interface definition
    #: (first element is the name of the interface, second is the modport name)
    #: into Topwrap's interface mode, usually as a result of
    #: :py:func:`_infer_modports`
    _modport_names: dict[tuple[str, str], InterfaceMode]

    #: List containing all interfaces parsed by frontend
    _parsed_intf: list[InterfaceDefinition]
    #: Interface names that currently use placeholder definitions.
    _placeholder_interfaces: set[str]

    def __init__(
        self,
        diag_log_level: ps.DiagnosticSeverity = ps.DiagnosticSeverity.Error,
        modules: Iterable[Module] = (),
        interfaces: Iterable[InterfaceDefinition] = (),
        src_man: Optional[ps.SourceManager] = None,
    ) -> None:
        self.src_man = ps.SourceManager() if src_man is None else src_man
        self._modules = {_ir_id_to_sv_str(m.id): m for m in modules}
        self._interfaces = {_ir_id_to_sv_str(itf.id): itf for itf in interfaces}
        self._submodules = {}
        self.diag_log_level = diag_log_level
        self._parsed_mods = {}
        self._typedefs = {}
        self._parsed_intf = []
        self._placeholder_interfaces = set()
        self._concat_modules: dict[int, Module] = {}  # concat modules of each size
        self._select_modules: dict[str, Module] = {}  # select modules by select name
        self._analysis_manager: Optional[ps.AnalysisManager] = None
        self._analysis_comp: Optional[ps.Compilation] = None
        # This may look like a useless operation, but this dictionary's
        # purpose is to store a mapping between SV modports and inferred
        # IR `InterfaceMode`. IR interfaces are loaded into this dict here
        # in this way just to be able to use a common code on both SV-parsed
        # and IR interfaces
        self._modport_names = {
            (iname, mode.value): mode for iname in self._interfaces for mode in InterfaceMode
        }

    def parse_tree(self, tree: ps.SyntaxTree) -> tuple[list[Module], list[InterfaceDefinition]]:
        """
        Parse a pyslang `SyntaxTree` into IR Modules

        :param tree: A group of SV sources parsed into a `SyntaxTree`
        """

        comp = ps.Compilation()
        comp.addSyntaxTree(tree)

        deng = ps.DiagnosticEngine(self.src_man)
        diags: Iterable[ps.Diagnostic] = comp.getAllDiagnostics()
        txtcli = ps.TextDiagnosticClient()
        deng.addClient(txtcli)

        for diag in diags:
            sev = deng.getSeverity(diag.code, diag.location)
            if sev.value >= self.diag_log_level.value:
                deng.issue(diag)
                logger.warning(
                    f"Slang diagnostic while parsing SystemVerilog sources: \n{txtcli.getString()}"
                )
                txtcli.clear()

        sym_queue = deque(comp.getRoot())

        while len(sym_queue) > 0:
            sym = sym_queue.popleft()
            # An `InstanceSymbol` is an instance of a module, interface
            # or program differentiated by `.isModule`, `.isInterface` etc.
            # In the AST there is no distinction between an instance and
            # a definition. All definitions are monomorphised with instances
            # with specific parameter values set.
            if isinstance(sym, ps.InstanceSymbol):
                self._visit_instance_ast(sym, comp, True)
                for csym in sym.body:
                    sym_queue.append(csym)
            # A `TypeAliasType` is a type alias. When encountered here it
            # specifically refers to a `typedef` construct. (But note that
            # this is not a concrete rule in other places of AST)
            elif isinstance(sym, ps.TypeAliasType):
                self._handle_typealias_ast(sym)
            # An assumption is made here that a compilation unit is basically
            # a wrapper for all modules, interfaces, packages, macros, etc. sharing
            # the same namespace context. So they're just treated as a container
            # for other symbols
            elif isinstance(sym, ps.CompilationUnitSymbol):
                for csym in sym:
                    sym_queue.append(csym)

        return (list(self._parsed_mods.values()), self._parsed_intf)

    def _ensure_analysis_manager(self, comp: ps.Compilation) -> ps.AnalysisManager:
        if self._analysis_manager is not None and self._analysis_comp is comp:
            return self._analysis_manager

        am = ps.AnalysisManager()
        am.analyze(comp)
        self._analysis_manager = am
        self._analysis_comp = comp
        return am

    def _replace_interface_definition_refs(
        self, old_def: InterfaceDefinition, new_def: InterfaceDefinition
    ) -> None:
        updated_signals = {sig._id: None for sig in new_def.signals}
        seen: set[ObjectId[Module]] = set()
        for mods in (self._parsed_mods.values(), self._submodules.values(), self._modules.values()):
            for mod in mods:
                if mod._id in seen:
                    continue
                seen.add(mod._id)
                for intf in mod.interfaces:
                    if intf.definition is not old_def:
                        continue
                    intf.definition = new_def
                    if len(intf.signals) == 0:
                        intf.signals = dict(updated_signals)

    def _visit_instance_ast(
        self, node: ps.InstanceSymbol, comp: ps.Compilation, addToModules: bool
    ):
        # An array of module/interface instances. Since they all
        # share the same base definition, it's enough to just handle
        # the first (or any) element.
        if isinstance(node, ps.InstanceArraySymbol):
            if isinstance(node[0], ps.InstanceSymbol):
                self._visit_instance_ast(node[0], comp, addToModules)
            return

        # An instance body contains ports, parameters and children
        # components. It can be possibly regarded as just a module
        # /interface definition (but not exactly, since different `InstanceSymbol`s
        # do not share the same `InstanceBodySymbol`)
        body: ps.InstanceBodySymbol = node.body
        if node.isInterface:
            if body.name in self._interfaces and body.name not in self._placeholder_interfaces:
                return
            prev = self._interfaces.get(body.name)
            ir_new_iface = self._parse_interface_ast(body)
            if prev is not None:
                self._replace_interface_definition_refs(prev, ir_new_iface)
                self._parsed_intf = [i for i in self._parsed_intf if i is not prev]
                self._placeholder_interfaces.discard(body.name)
            self._interfaces[body.name] = ir_new_iface
            self._parsed_intf.append(ir_new_iface)
        elif node.isModule:
            if addToModules:
                if body.name in self._modules:
                    return
                self._parsed_mods[body.name] = self._modules[body.name] = self._parse_module_ast(
                    node, comp
                )
            else:
                if body.name in self._submodules:
                    return
                self._submodules[body.name] = self._parse_module_ast(node, comp)

    def _handle_typealias_ast(self, node: ps.TypeAliasType):
        if node.targetType.typeSyntax is None:
            return
        typ = self._parse_var_type_cst(node.targetType.typeSyntax, node)
        typ.name = node.name
        if node.lexicalPath in self._typedefs:
            return
        self._typedefs[node.lexicalPath] = typ

    def _parse_module_ast(self, mod_ast: ps.InstanceSymbol, comp: ps.Compilation) -> Module:
        return _ModuleAstParserState(self, mod_ast, comp).parse()

    def _parse_interface_ast(self, intf_ast: ps.InstanceBodySymbol) -> InterfaceDefinition:
        signals = dict[str, InterfaceSignal]()
        id = Identifier(name=intf_ast.name)
        # `ModportPortSymbol` is a specific signal in a SV modport list
        # (e.g. "addr" in `modport axi_drv(output addr, input rdata);`)
        # while "axi_drv" itself is a `ModportSymbol`
        modports = dict[str, list[ps.ModportPortSymbol]]()
        for entry in intf_ast:
            if isinstance(entry, (ps.VariableSymbol, ps.NetSymbol)):
                ir_type = self._parse_var_type_ast(entry)
                signals[entry.name] = InterfaceSignal(
                    name=entry.name,
                    regexp=re.compile(entry.name),
                    type=ir_type,
                    # This ideologically matches behavior defined in "IEEE Standard for
                    # SystemVerilog—Unified Hardware Design, Specification, and Verification
                    # Language 2023 - Section 25.3.2 Interface example using a named bundle"
                    # where all signals are implicitly ref inout.
                    modes={
                        InterfaceMode.UNSPECIFIED: InterfaceSignalConfiguration(
                            required=False, direction=PortDirection.INOUT
                        )
                    },
                )
            elif isinstance(entry, ps.ModportSymbol):
                sigs = list[ps.ModportPortSymbol]()
                for sig in entry:
                    if isinstance(sig, ps.ModportPortSymbol):
                        sigs.append(sig)
                modports[entry.name] = sigs

        inf = _infer_modports(modports)
        for side in (InterfaceMode.MANAGER, InterfaceMode.SUBORDINATE):
            if (man := inf.get(side)) is not None:
                self._modport_names[(intf_ast.name, man)] = side
                for sig in modports[man]:
                    signals[sig.name].modes[side] = InterfaceSignalConfiguration(
                        required=False, direction=_slang_dir_to_ir_dir(sig.direction)
                    )

        return InterfaceDefinition(id=id, signals=signals.values())

    # `Symbol` is a base type for all AST objects
    def _parse_parameter_ast(self, param_ast: ps.Symbol) -> Optional[Parameter]:
        def_val = None
        # `ParameterSymbol` corresponds to `parameter [int,byte,logic,etc.] pname = 0,`
        # in SystemVerilog
        if isinstance(param_ast, ps.ParameterSymbol):
            # `DeclaratorSyntax` - the CST declaring something with a possible initializer value
            # (here the right hand side of "=") in a definition of a e.g. a module
            if not isinstance(param_ast.syntax, ps.DeclaratorSyntax):
                logger.error(
                    f"Expected DeclaratorSyntax, got: {param_ast.syntax} in {param_ast.lexicalPath}"
                )
                return
            if param_ast.syntax.initializer is not None:
                def_val = str(param_ast.syntax.initializer.expr).strip()
        # `TypeParameterSymbol` corresponds to `parameter type pname = logic`
        # in SystemVerilog
        elif isinstance(param_ast, ps.TypeParameterSymbol):
            if not isinstance(param_ast.targetType, ps.DeclaredType):
                logger.error(
                    f"Expected DeclaredType, got: {param_ast.targetType} in {param_ast.lexicalPath}"
                )
                return
            if param_ast.targetType.typeSyntax is not None:
                def_val = str(param_ast.targetType.typeSyntax).strip()
        else:
            logger.error(
                f"Unexpected parameter symbol AST type: '{type(param_ast)}' of "
                f"{param_ast.lexicalPath}"
            )
            return

        def_val = None if def_val is None else ElaboratableValue(def_val)
        return Parameter(name=param_ast.name, default_value=def_val)

    def _parse_var_type_ast(self, var: Union[ps.VariableSymbol, ps.NetSymbol]) -> Logic:
        # `FixedSizeUnpackedArrayType` - an unpacked array type, for example `logic var1[4][8];`
        if isinstance(var.type, ps.FixedSizeUnpackedArrayType):
            if not isinstance(var.syntax, ps.DeclaratorSyntax):
                logger.error(f"Expected DeclaratorSyntax, got: {var.syntax} in {var.lexicalPath}")
                return Bit()

            (*dims,) = self._extract_dimensions_cst(var.syntax.dimensions)
            for d in dims:
                # This is done due to the assumption of unpacked arrays being
                # indexed low-to-high. In case of a single-number unpacked dimension (e.g. [4]),
                # slang converts it to a low-to-high range starting from 0 as well ([0:3]).
                d.lower, d.upper = d.upper, d.lower
            return LogicArray(
                dimensions=dims,
                item=self._parse_var_type_cst(var.declaredType.typeSyntax, var).copy(),
            )

        return self._parse_var_type_cst(var.declaredType.typeSyntax, var)

    def _telescope_type_ast(self, sym: Any) -> Any:
        while isinstance(sym, ps.TypeAliasType):
            sym = sym.targetType.type
        return sym

    # `SyntaxNode` is a common base type for all CST objects, just like `Symbol`
    # is a base type for all AST objects
    def _extract_dimensions_cst(self, dim_node: ps.SyntaxNode) -> Iterator[Dimensions]:
        # `SyntaxNode.SyntaxKind` is a tag of the variant (as if a `SyntaxNode` was a tagged union)
        # of CST object. Some variants are only available as a kind, while some also have
        # a dedicated class that inherits from `SyntaxNode`...
        if dim_node.kind != ps.SyntaxKind.SyntaxList:
            logger.error(
                f"Expected dimensions to be a SyntaxList, got: {dim_node.kind} in {dim_node}"
            )
            return

        for dim in dim_node:
            if not isinstance(dim, ps.VariableDimensionSyntax) or not isinstance(
                spec := dim.specifier, ps.RangeDimensionSpecifierSyntax
            ):
                logger.error(f"Expected a VariableDimensionSyntax, got: {dim}")
                continue

            # A dimension defined by a single number - its size, e.g.: `logic var1[4];`
            if isinstance(spec.selector, ps.BitSelectSyntax):
                yield Dimensions(
                    upper=ElaboratableValue(str(spec.selector.expr)) - ElaboratableValue(1)
                )
            # A dimension defined by a bit range, e.g.: `logic var1[0:3];`
            elif isinstance(spec.selector, ps.RangeSelectSyntax):
                yield Dimensions(
                    upper=ElaboratableValue(str(spec.selector.left)),
                    lower=ElaboratableValue(str(spec.selector.right)),
                )
            else:
                logger.error(f"Unexpected dimensions selector: {type(spec.selector)}")

    def _parse_var_type_cst(self, syn: ps.SyntaxNode, sym: ps.Symbol) -> Logic:
        # All common SV base numerical types fall under `IntegerTypeSyntax`:
        # `logic`, `reg`, `bit`, etc.
        # `ImplicitTypeSyntax` is used for elements without an explicit type, e.g.
        # a net declaration: `wire [3:0] net1 = abc[3:0];`
        if isinstance(syn, (ps.IntegerTypeSyntax, ps.ImplicitTypeSyntax)):
            (*dims,) = self._extract_dimensions_cst(syn.dimensions)
            if len(dims) == 0:
                return Bit()
            else:
                return Bits(dimensions=dims)
        elif isinstance(syn, ps.StructUnionTypeSyntax):
            return self._parse_struct_type_cst(syn, sym)
        # `NamedTypeSyntax` refers to any type referenced by an alias
        # e.g. a name of a typedef or name of a `parameter type`
        elif isinstance(syn, ps.NamedTypeSyntax):
            return self._parse_type_alias_cst(syn, sym)
        elif isinstance(syn, ps.EnumTypeSyntax):
            return self._parse_enum_type_cst(syn, sym)
        else:
            logger.warning(
                f"Unexpected syntax type: '{type(syn)}' in '{sym.lexicalPath}'. Assuming `Bit()`"
            )
            return Bit()

    def _parse_struct_type_cst(self, syn: ps.StructUnionTypeSyntax, sym: ps.Symbol) -> Logic:
        (*dims,) = self._extract_dimensions_cst(syn.dimensions)
        fields = list[StructField[Logic]]()
        for mem in syn.members:
            if not isinstance(mem, ps.StructUnionMemberSyntax):
                logger.error(f"Unexpected type of struct member: {type(mem)} in {sym.lexicalPath}")
                continue

            mem_type = self._parse_var_type_cst(mem.type, sym)
            for decl in mem.declarators:
                if not isinstance(decl, ps.DeclaratorSyntax):
                    continue
                (*decl_dims,) = self._extract_dimensions_cst(decl.dimensions)
                if len(decl_dims) != 0:
                    fields.append(
                        StructField(
                            name=decl.name.valueText,
                            type=LogicArray(item=mem_type, dimensions=decl_dims),
                        )
                    )
                else:
                    fields.append(StructField(name=decl.name.valueText, type=mem_type.copy()))

        struct = BitStruct(fields=fields)
        return struct if dims == [] else LogicArray(item=struct, dimensions=dims)

    def _parse_type_alias_cst(self, syn: ps.NamedTypeSyntax, sym: ps.Symbol) -> Logic:
        if not isinstance(
            syn.name,
            # First is a plain name, second is a select operation on a plain name (dimensions)
            # third is a name with a scope, so e.g. `package::class::type_a`
            (ps.IdentifierNameSyntax, ps.IdentifierSelectNameSyntax, ps.ScopedNameSyntax),
        ):
            logger.error(f"Unexpected named type: {type(syn.name)} in {sym.lexicalPath}")
            return Bit()

        dims: list[Dimensions] = []
        dim_node = getattr(syn, "dimensions", None)
        if dim_node is not None:
            (*dims,) = self._extract_dimensions_cst(dim_node)

        name = str(syn.name)
        cleaned_name = _strip_sv_comments(name) or name.strip()
        lookup_name = _lookup_name_from_clean_alias(cleaned_name, name.strip())
        if not dims:
            dims.extend(_extract_dims_from_alias_text(cleaned_name))

        parent: ps.Scope = sym.parentScope
        try:
            typeref = parent.lookupName(lookup_name)
        except RuntimeError:
            typeref = None
        if typeref is None:
            fallback: Logic = Bit(name=lookup_name if lookup_name else name)
            logger.warning(
                f"Could not resolve type alias '{cleaned_name.strip()}' in '{sym.lexicalPath}'. The"
                f" file where it's defined or a macro that provides it were probably not"
                f" included in the fileset. Assuming type is a single-bit logic type."
            )
            return _logic_with_dims(fallback, dims)
        name = typeref.lexicalPath
        ir_type = self._typedefs.get(name)
        if ir_type is None:
            if isinstance(typeref, ps.TypeAliasType):
                self._handle_typealias_ast(typeref)
                ir_type = self._typedefs.get(name)
                if ir_type is None:
                    # Parameterized type parameters often have no concrete type syntax;
                    # keep such unresolved fallbacks anonymous for stable comparisons.
                    fallback = (
                        Bit()
                        if typeref.targetType.typeSyntax is None
                        else Bit(name=lookup_name if lookup_name else name)
                    )
                    logger.warning(
                        f"Could not parse concrete type for type alias '{name}'.\tIt probably"
                        f" is a `parameter type` on a module or interface. Assuming type is a"
                        f" single-bit logic type."
                    )
                    return _logic_with_dims(fallback, dims)
        if ir_type is None:
            fallback = Bit(name=lookup_name if lookup_name else name)
            logger.warning(
                "Could not parse concrete type for type alias '%s'. Assuming single-bit logic.",
                name,
            )
            return _logic_with_dims(fallback, dims)
        return _logic_with_dims(ir_type.copy(), dims)

    def _parse_enum_type_cst(self, syn: ps.EnumTypeSyntax, sym: ps.Symbol) -> Enum:
        (*dims,) = self._extract_dimensions_cst(syn.dimensions)
        base_type = self._parse_var_type_cst(syn.baseType, sym)
        if isinstance(base_type, LogicArray):
            dims.extend(base_type.dimensions)
        resolved = self._telescope_type_ast(sym)
        if isinstance(resolved, ps.EnumType):
            dims = [Dimensions(upper=ElaboratableValue(resolved.bitWidth - 1)), *dims]

        prev = None
        variants = {}
        for member in syn.members:
            if isinstance(member, ps.DeclaratorSyntax):
                if member.initializer is not None:
                    val = ElaboratableValue(str(member.initializer.expr).strip())
                else:
                    val = ElaboratableValue(0) if prev is None else prev + ElaboratableValue(1)
                variants[member.name.valueText] = prev = val

        return Enum(
            variants=variants,
            dimensions=dims,
        )
