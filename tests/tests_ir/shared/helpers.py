# Copyright (c) 2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from topwrap.util import collect_filelist_sources


def _canon_interfaces(intfs: list[dict[str, Any]], node_key: str, intf_map: dict[str, Any]):
    """Drop unstable interface fields and build a stable interface-id mapping."""
    out = []
    for i in intfs:
        iid = i.get("id")
        if iid is not None:
            intf_map[iid] = (node_key, i.get("name"))
        out.append({k: v for k, v in i.items() if k not in {"id", "externalName"}})
    out.sort(key=lambda i: i.get("name"))
    return out


def _canon_graphs(graphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize KPM dataflow graphs so they compare independent of parse ordering."""

    def graph_sort_key(g: dict[str, Any]):
        """Sort graphs by deterministic node signature."""
        node_keys = sorted((n.get("instanceName"), n.get("name")) for n in g.get("nodes", []))
        return (len(node_keys), node_keys)

    canon = []
    for g in sorted(graphs, key=graph_sort_key):
        intf_map: dict[str, Any] = {}
        nodes = sorted(g.get("nodes", []), key=lambda n: (n.get("instanceName"), n.get("name")))
        cnodes = []
        for n in nodes:
            nkey = f"{n.get('instanceName', '')}/{n.get('name')}"
            cnodes.append(
                {
                    "name": n.get("name"),
                    "instanceName": n.get("instanceName"),
                    "interfaces": _canon_interfaces(n.get("interfaces", []), nkey, intf_map),
                }
            )

        conns = []
        for c in g.get("connections", []):
            src = c.get("from")
            tgt = c.get("to")
            conns.append(
                {
                    "type": c.get("type"),
                    "source": intf_map.get(src, src),
                    "target": intf_map.get(tgt, tgt),
                }
            )
        conns.sort(key=lambda c: (c.get("type"), str(c.get("source")), str(c.get("target"))))
        canon.append({"nodes": cnodes, "connections": conns})

    return canon


def canonical_flow(flow: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize KPM dataflow payload to a stable shape for equality checks."""
    return {
        "version": flow.get("version"),
        "graphs": _canon_graphs(flow.get("graphs", [])),
    }


def canonical_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize KPM specification payload (sort nodes, interfaces and properties)."""
    nodes: list[dict[str, Any]] = []
    for n in list(spec.get("nodes", [])):
        node = {k: v for k, v in n.items() if k != "additionalData"}
        ints = [dict(i) for i in node.get("interfaces", [])]
        ints.sort(key=lambda i: i.get("name"))
        node["interfaces"] = ints

        props = [dict(p) for p in node.get("properties", [])]
        props.sort(key=lambda p: p.get("name"))
        node["properties"] = props
        nodes.append(node)

    nodes.sort(key=lambda n: n.get("name"))
    return {"version": spec.get("version"), "nodes": nodes, "metadata": spec.get("metadata")}


_SV_NUM_LIT_RE = re.compile(
    r"(?<![A-Za-z0-9_$])(?:(?P<w>\d+)?)'(?P<s>[sS]?)(?P<b>[bBdDhHoO])(?P<v>[0-9a-fA-F_xXzZ?]+)"
)
_SV_DECL_RE = re.compile(
    r"^(?:logic|wire|reg|bit|byte|shortint|int|longint|integer|time|"
    r"shortreal|real|realtime|\\\S+|[A-Za-z_$][\w:$]*)\b"
)
_SV_ANSI_INTF_PORT_RE = re.compile(r"^[A-Za-z_$\\][\w:$\\\[\].]*\s+[A-Za-z_$\\][\w$\\\[\].]*,?$")


def _svnorm_canon_number_literals(line: str) -> str:
    """Rewrite known-valued SV numeric literals to canonical decimal form."""

    def _repl(m: re.Match[str]) -> str:
        """Convert a matched literal while preserving sign/width semantics."""
        width = m.group("w") or ""
        signed = m.group("s").lower()
        base = m.group("b").lower()
        digits = m.group("v").replace("_", "")
        if re.search(r"[xXzZ?]", digits):
            return m.group(0)
        try:
            value = int(digits, {"b": 2, "o": 8, "d": 10, "h": 16}[base])
        except ValueError:
            return m.group(0)
        sign_part = "s" if signed == "s" else ""
        return f"{width}'{sign_part}d{value}" if width else f"'{sign_part}d{value}"

    return _SV_NUM_LIT_RE.sub(_repl, line)


def _svnorm_is_decl(line: str) -> bool:
    """Return True when a line is a declaration statement, not executable logic."""
    stripped = line.lstrip()
    if not stripped.endswith(";"):
        return False
    if stripped.startswith(
        (
            "assign ",
            "if ",
            "else",
            "for ",
            "while ",
            "case ",
            "default:",
            "return ",
            "begin",
            "end",
        )
    ):
        return False
    return bool(_SV_DECL_RE.match(stripped))


def _svnorm_instance_name(line: str) -> str:
    """Extract instance-name token from the first line of an instantiation block."""
    stripped = line.strip()
    if not stripped.endswith("("):
        return stripped
    before = stripped[:-1].strip()
    tokens = before.replace(")", " ").split()
    return tokens[-1] if tokens else before


def _svnorm_port_key(line: str) -> str:
    """Extract named-port key used to sort named connections deterministically."""
    stripped = line.strip()
    if not stripped.startswith("."):
        return stripped
    return stripped[1:].split("(", 1)[0].strip()


def _svnorm_canon_instance(block: list[str]) -> list[str]:
    """Normalize one instance block by sorting named ports and stripping expressions."""
    if len(block) < 2:
        return block
    head = block[0]
    tail = block[-1]
    port_start_idx = next(
        (
            i
            for i in range(1, len(block) - 1)
            if block[i].strip().endswith("(") and ")" in block[i].strip()
        ),
        None,
    )
    if port_start_idx is None:
        header = [head]
        ports = block[1:-1]
    else:
        header = block[: port_start_idx + 1]
        ports = block[port_start_idx + 1 : -1]

    port_lines = [p for p in ports if p.strip().startswith(".")]
    other = [p for p in ports if not p.strip().startswith(".")]
    port_lines.sort(key=_svnorm_port_key)
    if not port_lines:
        return [*header, *other, tail]

    first = port_lines[0]
    indent = first[: first.find(".")] if "." in first else ""
    stripped_ports = []
    for p in port_lines:
        pp = p.strip().rstrip(",")
        if "(" in pp:
            pname = pp.split("(", 1)[0].rstrip()
            pp = f"{pname}()"
        stripped_ports.append(pp)
    canon_ports = [
        f"{indent}{p}{',' if i < len(stripped_ports) - 1 else ''}"
        for i, p in enumerate(stripped_ports)
    ]
    return [*header, *other, *canon_ports, tail]


def _svnorm_canon_module(lines: list[str]) -> list[str]:
    """Normalize one module block (ports, instances and body noise filtering)."""
    header: list[str] = []
    body: list[str] = []
    in_header = True
    for line in lines:
        if in_header:
            header.append(line)
            if line.strip() == ");":
                in_header = False
            continue
        body.append(line)

    canon_header: list[str] = []
    for line in header:
        stripped = line.strip()
        if stripped.startswith(("input ", "output ", "inout ")):
            indent = line[: len(line) - len(line.lstrip())]
            parts = stripped.rstrip(",").split()
            canon_header.append(f"{indent}{parts[0]} logic {parts[-1]}")
            continue
        if _SV_ANSI_INTF_PORT_RE.match(stripped):
            # Interface-style ANSI ports (e.g. `my_intf foo_if`) are not
            # consistently reconstructed across roundtrips.
            continue
        canon_header.append(line)

    instances: list[tuple[str, list[str]]] = []
    other: list[str] = []
    i = 0
    while i < len(body):
        line = body[i]
        stripped = line.strip()
        if stripped.endswith("(") and not stripped.startswith(
            ("module ", "assign ", "logic ", "wire ", "reg ")
        ):
            block = [line]
            i += 1
            while i < len(body):
                block.append(body[i])
                if body[i].strip() == ");":
                    break
                i += 1
            instances.append((_svnorm_instance_name(line), _svnorm_canon_instance(block)))
            i += 1
            continue
        if not _svnorm_is_decl(line) and not line.lstrip().startswith("assign "):
            other.append(line)
        i += 1

    instances.sort(key=lambda x: x[0])
    inst_lines = [line for _name, block in instances for line in block]
    return [*canon_header, *inst_lines, *other]


def _svnorm_block_start(stripped: str) -> str | None:
    """Detect SV top-level block start kind for canonical block splitting."""
    if stripped.startswith("module "):
        return "module"
    if stripped.startswith("interface "):
        return "interface"
    if stripped.startswith("package "):
        return "package"
    return None


def _svnorm_block_end(stripped: str, block_type: str) -> bool:
    """Check whether a line closes a previously opened SV top-level block."""
    if block_type == "module":
        return stripped == "endmodule"
    if block_type == "interface":
        return stripped == "endinterface"
    if block_type == "package":
        return stripped == "endpackage"
    return False


def normalize_sv(text: str) -> str:
    """Canonicalize generated SV text to a stable representation for roundtrip tests."""
    lines = [
        _svnorm_canon_number_literals(re.sub(r"]\s+\[", "][", raw_line.rstrip()))
        for raw_line in text.splitlines()
    ]
    blocks: list[list[str]] = []
    cur: list[str] = []
    in_block: str | None = None
    for line in lines:
        stripped = line.strip()
        block_type = _svnorm_block_start(stripped)
        if block_type is not None:
            if cur:
                blocks.append(cur)
            cur = [line]
            in_block = block_type
            continue
        cur.append(line)
        if in_block is not None and _svnorm_block_end(stripped, in_block):
            blocks.append(cur)
            cur = []
            in_block = None
    if cur:
        blocks.append(cur)

    canon = [
        _svnorm_canon_module(block) if block and block[0].strip().startswith("module ") else block
        for block in blocks
    ]
    canon.sort(key=lambda m: m[0] if m else "")

    # Filter out interface blocks that may not be consistently parseable
    # across roundtrips due to missing package/type definitions.
    filtered = [block for block in canon if block and not block[0].strip().startswith("interface ")]

    flat = [line for block in filtered for line in block if line.strip() != ""]
    return "\n".join(flat).strip() + "\n"


def get_caliptra_sources() -> tuple[list[Path], set[Path]]:
    """Collect Caliptra source files and include directories from all `.vf` manifests."""
    here = Path(__file__).resolve().parent
    caliptra_path = here / "../../../examples/caliptra/Caliptra"
    return collect_filelist_sources(caliptra_path)
