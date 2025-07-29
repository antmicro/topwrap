# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import re
from datetime import datetime
from functools import reduce
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from topwrap.model.hdl_types import (
    Bit,
    BitStruct,
    Enum,
    Logic,
    LogicArray,
    LogicBitSelect,
    LogicFieldSelect,
    LogicSelect,
)
from topwrap.model.misc import TranslationError

TEMPLATE = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    trim_blocks=True,
    lstrip_blocks=False,
)

SV_KEYWORDS = {
    "alias", "accept_on", "always_comb", "always", "always_latch", "always_ff",
    "assert", "and", "assume", "assign", "before", "automatic", "bind", "begin",
    "binsof", "bins", "break", "bit", "bufif0", "buf", "byte", "bufif1", "casex",
    "case", "cell", "casez", "checker", "chandle", "clocking", "class", "config",
    "cmos", "constraint", "const", "continue", "context", "covergroup", "cover",
    "cross", "coverpoint", "default", "deassign", "design", "defparam", "dist",
    "disable", "edge", "do", "end", "else", "endchecker", "endcase", "endclocking",
    "endclass", "endfunction", "endconfig", "endgroup", "endgenerate", "endmodule",
    "endinterface", "endprimitive", "endpackage", "endproperty", "endprogram",
    "endsequence", "endspecify", "endtask", "endtable", "event", "enum", "expect",
    "eventually", "extends", "export", "final", "extern", "for", "first_match",
    "foreach", "force", "fork", "forever", "function", "forkjoin", "genvar",
    "generate", "highz0", "global", "if", "highz1", "ifnone", "iff", "illegal_bins",
    "ignore_bins", "implies", "implements", "incdir", "import", "initial", "include",
    "input", "inout", "instance", "inside", "integer", "int", "interface", "interconnect",
    "join", "intersect", "join_none", "join_any", "let", "large", "library", "liblist",
    "localparam", "local", "longint", "logic", "matches", "macromodule", "modport",
    "medium", "nand", "module", "nettype", "negedge", "nexttime", "new", "nor", "nmos",
    "not", "noshowcancelled", "notif1", "notif0", "or", "null", "package", "output",
    "parameter", "packed", "posedge", "pmos", "priority", "primitive", "property", "program",
    "pull0", "protected", "pulldown", "pull1", "pulsestyle_ondetect", "pullup", "pure",
    "pulsestyle_onevent", "randc", "rand", "randsequence", "randcase", "real", "rcmos",
    "ref", "realtime", "reject_on", "reg", "repeat", "release", "return", "restrict",
    "rpmos", "rnmos", "rtranif0", "rtran", "s_always", "rtranif1", "s_nexttime",
    "s_eventually", "s_until_with", "s_until", "sequence", "scalared", "shortreal",
    "shortint", "signed", "showcancelled", "soft", "small", "specify", "solve", "static",
    "specparam", "strong", "string", "strong1", "strong0", "super", "struct", "supply1",
    "supply0", "sync_reject_on", "sync_accept_on", "tagged", "table", "this", "task", "time",
    "throughout", "timeunit", "timeprecision", "tranif0", "tran", "tri", "tranif1", "tri1",
    "tri0", "trior", "triand", "type", "trireg", "union", "typedef", "unique0", "unique",
    "until", "unsigned", "untyped", "until_with", "uwire", "use", "vectored", "var", "void",
    "virtual", "wait_order", "wait", "weak", "wand", "weak1", "weak0", "wildcard", "while",
    "with", "wire", "wor", "within", "xor", "xnor"
}  # fmt: skip


def get_template(name: str) -> Template:
    TEMPLATE.filters["sv_var"] = sv_varname
    return TEMPLATE.get_template(
        name,
        globals={
            "gen_date": datetime.now,
            sv_varname.__name__: sv_varname,
            serialize_type.__name__: serialize_type,
        },
    )


def sv_varname(base: str) -> str:
    """
    Sanitizes user-defined identifiers in accordance with the
    "IEEE Standard for SystemVerilog—Unified Hardware
    Design, Specification, and Verification Language 2023"
    Section 5.6.1 - Escaped identifiers
    """

    if not base.startswith("\\"):
        base = re.sub(r"\s", "_", base)
        if re.search(r"^[^A-Za-z_]|[^A-Za-z0-9$_]", base) or base in SV_KEYWORDS:
            base = rf"\{base} "
    return base[:1023]


def serialize_type(logic: Logic, indent: int = 0, tld: bool = False) -> str:
    """
    Serializes an IR HDL type definition into SV snippet appropriate
    to use wherever a type is required in the generated code
    """

    if logic.name is not None and not tld:
        return sv_varname(logic.name)

    if isinstance(logic, Bit):
        return "logic"
    elif isinstance(logic, Enum):
        return (
            "enum {\n"
            + ",\n".join(
                f"{' ' * (indent + 4)}{sv_varname(name)} = {value}"
                for name, value in logic.variants.items()
            )
            + f"\n{' ' * indent}}}"
        )
    elif isinstance(logic, LogicArray):
        return (
            serialize_type(logic.item, indent)
            + " "
            + reduce(lambda a, b: f"{a}[{b.upper.value}:{b.lower.value}]", logic.dimensions, "")
        )
    elif isinstance(logic, BitStruct):
        if logic.name is None or tld:
            return (
                "struct packed {\n"
                + "\n".join(
                    (
                        f"{' ' * (indent + 4)}{serialize_type(f.type, indent + 4, tld=False)}"
                        f" {sv_varname(f.field_name)};"
                    )
                    for f in logic.fields
                )
                + f"\n{' ' * indent}}}"
            )
        else:
            return sv_varname(logic.name)

    raise TranslationError(f"Unexpected type to serialize: {type(logic)}")


def serialize_select(select: LogicSelect) -> str:
    """Serializes a selection operation (e.g. on a port or a net) into an SV snippet"""

    out = ""
    for subsel in select.ops:
        if isinstance(subsel, LogicFieldSelect):
            out += f".{sv_varname(subsel.field.field_name)}"
        elif isinstance(subsel, LogicBitSelect):
            out += f"[{subsel.slice.upper}:{subsel.slice.lower}]"
    return out
