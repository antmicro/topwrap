# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Union

import pyslang as ps

from topwrap.backend.sv.common import sv_varname
from topwrap.model.connections import Port, PortDirection
from topwrap.model.hdl_types import (
    Bit,
    Bits,
    BitStruct,
    Dimensions,
    Enum,
    Logic,
    LogicArray,
    StructField,
)
from topwrap.model.interface import (
    Interface,
    InterfaceDefinition,
    InterfaceMode,
    InterfaceSignal,
    InterfaceSignalConfiguration,
)
from topwrap.model.misc import ElaboratableValue, FileReference, Identifier, Parameter
from topwrap.model.module import Module
from topwrap.util import MISSING, UnreachableError

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


class SystemVerilogSlangParser:
    src_man: ps.SourceManager
    diag_log_level: ps.DiagnosticSeverity

    #: A dictionary of preloaded IR Modules whose instances
    #: can be encountered in the SV sources.
    #: Keyed by :py:meth:`_ir_id_to_sv_str`
    _modules: dict[str, Module]

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
        self.diag_log_level = diag_log_level
        self._parsed_mods = {}
        self._typedefs = {}
        self._parsed_intf = []
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
                self._visit_instance_ast(sym)
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

    def _visit_instance_ast(self, node: ps.InstanceSymbol):
        # An array of module/interface instances. Since they all
        # share the same base definition, it's enough to just handle
        # the first (or any) element.
        if isinstance(node, ps.InstanceArraySymbol):
            if isinstance(node[0], ps.InstanceSymbol):
                self._visit_instance_ast(node[0])
            return

        # An instance body contains ports, parameters and children
        # components. It can be possibly regarded as just a module
        # /interface definition (but not exactly, since different `InstanceSymbol`s
        # do not share the same `InstanceBodySymbol`)
        body: ps.InstanceBodySymbol = node.body
        if node.isInterface:
            if body.name in self._interfaces:
                return
            ir_new_iface = self._parse_interface_ast(body)
            self._interfaces[body.name] = ir_new_iface
            self._parsed_intf.append(ir_new_iface)
        elif node.isModule:
            if body.name in self._modules:
                return
            self._parsed_mods[body.name] = self._modules[body.name] = self._parse_module_ast(node)

    def _handle_typealias_ast(self, node: ps.TypeAliasType):
        if node.targetType.typeSyntax is None:
            return
        typ = self._parse_var_type_cst(node.targetType.typeSyntax, node)
        typ.name = node.name
        if node.lexicalPath in self._typedefs:
            return
        self._typedefs[node.lexicalPath] = typ

    def _parse_module_ast(self, mod_ast: ps.InstanceSymbol) -> Module:
        body: ps.InstanceBodySymbol = mod_ast.body

        id = Identifier(name=body.name)
        mod = Module(id=id)

        for param_ast in body.parameters:
            param = self._parse_parameter_ast(param_ast)
            if param is not None:
                mod.add_parameter(param)

        for port_ast in body.portList:
            # What the name implies, an external interface IO on a module
            # using the SystemVerilog `interface` construct
            if isinstance(port_ast, ps.InterfacePortSymbol):
                if port_ast.interfaceDef is None:
                    logger.warning(
                        f"There is no interface definition in provided sources"
                        f" for interface '{port_ast.lexicalPath}'"
                    )
                    continue
                for conn in port_ast.connection:
                    if isinstance(conn, ps.InstanceSymbol):
                        self._visit_instance_ast(conn)
                name = port_ast.interfaceDef.name
                idef = self._interfaces[name]
                mode = self._modport_names.get((name, port_ast.modport))
                if mode is None:
                    mode = InterfaceMode.UNSPECIFIED
                inst = Interface(
                    name=port_ast.name,
                    mode=mode,
                    definition=idef,
                    signals={s._id: None for s in idef.signals},
                )
                mod.add_interface(inst)
            else:
                # If this port is not an interface port, then it must be a plain port.
                # A port definition in the AST simultaneously declares a variable or a net,
                # as if `logic port_name;` or `wire port_name;` was manually
                # declared in the module body
                if not isinstance(port_ast, ps.PortSymbol) or not isinstance(
                    port_ast.internalSymbol, (ps.VariableSymbol, ps.NetSymbol)
                ):
                    logger.error(
                        f"Exotic port symbol: {port_ast}, "
                        f"{getattr(port_ast, 'internalSymbol', MISSING)}"
                    )
                    continue

                port = Port(
                    name=port_ast.name,
                    direction=_slang_dir_to_ir_dir(port_ast.direction),
                    type=self._parse_var_type_ast(port_ast.internalSymbol),
                )

                mod.add_port(port)

        # TODO: can we include imported packages as dependencies as well?
        file = Path(self.src_man.getFileName(body.location))
        line = self.src_man.getLineNumber(body.location)
        column = self.src_man.getColumnNumber(body.location)

        mod.add_reference(FileReference(file=file, line=line, column=column))

        return mod

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

        name = str(syn.name)
        parent: ps.Scope = sym.parentScope
        typeref = parent.lookupName(name)
        if typeref is None:
            logger.warning(
                f"Could not resolve type alias '{name.strip()}' in '{sym.lexicalPath}'. The"
                f" file where it's defined or a macro that provides it were probably not"
                f" included in the fileset. Assuming type is a single-bit logic type."
            )
            return Bit()
        name = typeref.lexicalPath
        ir_type = self._typedefs.get(name)
        if ir_type is None:
            if isinstance(typeref, ps.TypeAliasType):
                self._handle_typealias_ast(typeref)
                ir_type = self._typedefs.get(name)
                if ir_type is None:
                    logger.warning(
                        f"Could not parse concrete type for type alias '{name}'.\tIt probably"
                        f" is a `parameter type` on a module or interface. Assuming type is a"
                        f" single-bit logic type."
                    )
                    return Bit()
        if ir_type is None:
            raise UnreachableError("ir_type is None was handled above")
        return ir_type

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
