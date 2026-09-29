#!/usr/bin/env python3
"""Generate design/INDEX.md from design/fleet_dev.pen.

The .pen file is plain JSON, so this needs only the Python standard library.
Run from the repo root after changing the design:

    python3 design/tools/pen_index.py
"""
import collections
import json
import re
from pathlib import Path

DESIGN = Path(__file__).resolve().parent.parent
PEN = DESIGN / "fleet_dev.pen"
OUT = DESIGN / "INDEX.md"


def walk(node):
    yield node
    for child in node.get("children") or []:
        yield from walk(child)


def texts(node):
    return [n["content"] for n in walk(node) if n.get("type") == "text" and n.get("content")]


def slot_label(node, names):
    """A slot's `slot` value lists the components suggested for it (may be empty)."""
    label = f"`{node['name']}` ({node['id']})"
    suggested = [names.get(ref, ref) for ref in node["slot"] or []]
    return f"{label}: {' / '.join(suggested)}" if suggested else label


def size(node):
    w, h = node.get("width"), node.get("height")
    fmt = lambda v: str(v) if isinstance(v, (int, float)) else "auto"
    return f"{fmt(w)}×{fmt(h)}"


def main():
    doc = json.loads(PEN.read_text())
    top = doc["children"]
    by_name = {f["name"]: f for f in top}

    # Instances also live inside override maps (`descendants`, slot fills), so
    # search every object in the document, not just the children tree.
    refs = collections.Counter()

    def count_refs(value):
        if isinstance(value, dict):
            if value.get("type") == "ref" and "ref" in value:
                refs[value["ref"]] += 1
            for v in value.values():
                count_refs(v)
        elif isinstance(value, list):
            for v in value:
                count_refs(v)

    count_refs(top)

    panels = sorted(
        (f for f in top if f["name"].startswith("Library ·")),
        key=lambda p: int(re.search(r"· (\d+)", p["name"]).group(1)),
    )
    components = [f for f in top if f.get("reusable")]
    names = {c["id"]: c["name"] for c in components}
    flow_screen = re.compile(r"^F(\d+)\.(\d+) ")
    flow_header = re.compile(r"^Flow (\d+) — ")
    flow_notes = re.compile(r"^Flow (\d+) · Step notes$")
    reference = [
        f for f in top
        if not f.get("reusable")
        and not f["name"].startswith("Library ·")
        and not flow_screen.match(f["name"])
        and not flow_header.match(f["name"])
        and not flow_notes.match(f["name"])
        and f["name"] != "User Flows — Index"
    ]

    lines = [
        "# Design index",
        "",
        "Generated from `fleet_dev.pen` by `design/tools/pen_index.py`. Do not edit by hand.",
        "",
        f"- Top-level frames: {len(top)}",
        f"- Reusable components: {len(components)} ({sum(refs[c['id']] for c in components)} references, nested ones included)",
        f"- Reference screens and boards: {len(reference)}",
        f"- Flow screens: {sum(1 for f in top if flow_screen.match(f['name']))}",
        "",
        "Node IDs are stable Pencil IDs; use them to find a node in the file (`\"id\": \"<ID>\"`).",
        "",
        "## Variables",
        "",
        "| Token | Type | Value |",
        "|---|---|---|",
    ]
    for name, var in doc.get("variables", {}).items():
        lines.append(f"| `{name}` | {var.get('type')} | `{var.get('value')}` |")

    lines += ["", "## Components", ""]
    placed = set()
    for p in panels:
        y0, y1 = p["y"], p["y"] + p["height"]
        members = sorted(
            (c for c in components if y0 <= c.get("y", 0) < y1),
            key=lambda c: (c["y"], c["x"]),
        )
        lines += [f"### {p['name'].split('· ', 1)[1]}", "", "| Component | ID | Size | Slots | Refs |", "|---|---|---|---|---|"]
        for c in members:
            placed.add(c["id"])
            slots = ", ".join(slot_label(n, names) for n in walk(c) if n.get("slot") is not None)
            lines.append(f"| {c['name']} | `{c['id']}` | {size(c)} | {slots} | {refs[c['id']]} |")
        lines.append("")
    orphans = [c for c in components if c["id"] not in placed]
    if orphans:
        lines += ["### Not on a library panel", ""]
        lines += [f"- {c['name']} (`{c['id']}`)" for c in orphans]
        lines.append("")

    lines += ["## Reference screens and boards", "", "| Frame | ID | Size |", "|---|---|---|"]
    for f in sorted(reference, key=lambda f: (f["y"], f["x"])):
        lines.append(f"| {f['name']} | `{f['id']}` | {size(f)} |")

    lines += ["", "## User flows", ""]
    headers = sorted(
        ((int(flow_header.match(f["name"]).group(1)), f) for f in top if flow_header.match(f["name"])),
        key=lambda t: t[0],
    )
    for num, header in headers:
        t = texts(header)
        description = t[2] if len(t) > 2 else ""
        screens = sorted(
            (f for f in top if (m := flow_screen.match(f["name"])) and int(m.group(1)) == num),
            key=lambda f: int(flow_screen.match(f["name"]).group(2)),
        )
        # Step notes read: "STEP n", title, trigger, repeated.
        notes = texts(by_name.get(f"Flow {num} · Step notes", {}))
        triggers = {}
        for i, s in enumerate(notes):
            m = re.match(r"STEP (\d+)$", s)
            if m and i + 2 < len(notes):
                triggers[int(m.group(1))] = notes[i + 2]
        lines += [
            f"### {header['name']}",
            "",
            description,
            "",
            "| Screen | ID | Size | Leads on when… |",
            "|---|---|---|---|",
        ]
        for s in screens:
            step = int(flow_screen.match(s["name"]).group(2))
            lines.append(f"| {s['name']} | `{s['id']}` | {size(s)} | {triggers.get(step, '')} |")
        lines.append("")

    OUT.write_text("\n".join(lines).rstrip() + "\n")
    print(f"wrote {OUT.relative_to(DESIGN.parent)}")


if __name__ == "__main__":
    main()
