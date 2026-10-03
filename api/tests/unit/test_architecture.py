"""The import and transaction rules of standard §7 and §11.2, checked statically.

- core/ never imports a feature.
- A feature imports another feature only through that feature's public.py.
- The feature import graph has no cycles.
- repository.py, public.py and jobs.py never commit, roll back or open a session.
"""

import ast
from pathlib import Path

PKG = "app"
SRC = Path(__file__).resolve().parents[2] / "src" / PKG
NO_TXN_FILES = {"repository.py", "public.py", "jobs.py"}
SESSION_FACTORIES = {"AsyncSession", "async_sessionmaker"}


def _modules() -> dict[Path, ast.Module]:
    return {p: ast.parse(p.read_text(), str(p)) for p in SRC.rglob("*.py")}


def _imports(tree: ast.Module) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            # The full path of each imported name: `from <pkg>.features.x import public` and
            # `from <pkg>.features.x.public import f` are both a door import.
            out += [f"{node.module}.{a.name}" for a in node.names]
    return out


def _feature_of(path: Path) -> str | None:
    parts = path.relative_to(SRC).parts
    return parts[1] if parts[0] == "features" and len(parts) > 2 else None


def test_core_imports_no_feature() -> None:
    bad = [
        f"{p.relative_to(SRC)} imports {m}"
        for p, tree in _modules().items()
        if p.relative_to(SRC).parts[0] == "core"
        for m in _imports(tree)
        if m.startswith(f"{PKG}.features")
    ]
    assert not bad, "core/ must not import features:\n" + "\n".join(bad)


def test_features_meet_only_through_public() -> None:
    bad = []
    for p, tree in _modules().items():
        mine = _feature_of(p)
        if mine is None:
            continue
        for m in _imports(tree):
            parts = m.split(".")
            other = parts[:2] == [PKG, "features"] and len(parts) > 2 and parts[2] != mine
            if other and (len(parts) < 4 or parts[3] != "public"):
                bad.append(f"{p.relative_to(SRC)} imports {m}")
    assert not bad, "import other features only through their public.py:\n" + "\n".join(bad)


def test_feature_graph_has_no_cycles() -> None:
    edges: dict[str, set[str]] = {}
    for p, tree in _modules().items():
        mine = _feature_of(p)
        if mine is None:
            continue
        for m in _imports(tree):
            parts = m.split(".")
            if parts[:2] == [PKG, "features"] and len(parts) > 2 and parts[2] != mine:
                edges.setdefault(mine, set()).add(parts[2])

    def visit(node: str, path: list[str]) -> None:
        if node in path:
            raise AssertionError("feature import cycle: " + " -> ".join([*path, node]))
        for nxt in edges.get(node, ()):
            visit(nxt, [*path, node])

    for start in edges:
        visit(start, [])


def test_only_services_control_transactions() -> None:
    bad = []
    for p, tree in _modules().items():
        if p.name not in NO_TXN_FILES:
            continue
        where = p.relative_to(SRC)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in {"commit", "rollback", "begin"}:
                bad.append(f"{where}:{node.lineno} calls .{func.attr}()")
            if isinstance(func, ast.Name) and func.id in SESSION_FACTORIES:
                bad.append(f"{where}:{node.lineno} creates a session")
    assert not bad, (
        "repositories, doors and job handlers flush; only services commit:\n" + "\n".join(bad)
    )
