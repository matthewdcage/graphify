"""Resolve graphify-out/graph.json from the active project and start the MCP server."""
from __future__ import annotations

import os
from pathlib import Path

from graphify.paths import GRAPHIFY_OUT
_WORKSPACE_ENV_KEYS = ("WORKSPACE_FOLDER", "CURSOR_PROJECT_DIR")
_START_ENV_KEYS = ("CURSOR_PROJECT_DIR", "WORKSPACE_FOLDER", "VSCODE_CWD", "PWD")


def find_graph_json(start: str | Path, *, stop_at: str | Path | None = None) -> Path | None:
    """Walk upward from start for graphify-out/graph.json, never above stop_at."""
    try:
        directory = Path(start).expanduser().resolve()
    except OSError:
        return None

    boundary = Path(stop_at).expanduser().resolve() if stop_at else None

    while True:
        candidate = directory / GRAPHIFY_OUT / "graph.json"
        if candidate.is_file():
            return candidate
        if boundary is not None and directory == boundary:
            return None
        if directory == directory.parent:
            return None
        directory = directory.parent


def resolve_workspace_boundary() -> Path | None:
    """Outermost workspace folder Cursor/VS Code exposes for this session."""
    for key in _WORKSPACE_ENV_KEYS:
        value = os.environ.get(key, "").strip()
        if value:
            return Path(value).expanduser().resolve()
    return None


def resolve_search_start(boundary: Path | None) -> Path:
    """Best-effort starting directory for an upward search within the workspace."""
    for key in _START_ENV_KEYS:
        value = os.environ.get(key, "").strip()
        if not value:
            continue
        start = Path(value).expanduser().resolve()
        if boundary is not None:
            try:
                start.relative_to(boundary)
                return start
            except ValueError:
                continue
        return start
    return (boundary or Path.cwd()).resolve()


def expected_graph_path(boundary: Path | None) -> Path:
    if boundary is not None:
        return boundary / GRAPHIFY_OUT / "graph.json"
    return Path(GRAPHIFY_OUT) / "graph.json"


def resolve_graph_path() -> str:
    """Pick the graph.json for the active workspace only (no parent monorepo fallback)."""
    explicit = os.environ.get("GRAPHIFY_GRAPH", "").strip()
    if explicit:
        return explicit

    boundary = resolve_workspace_boundary()
    start = resolve_search_start(boundary)
    stop_at = boundary or start

    found = find_graph_json(start, stop_at=stop_at)
    if found:
        return str(found)

    return str(expected_graph_path(boundary))


def resolve_workspace_roots() -> list[str]:
    """Collect distinct workspace directory hints from environment."""
    roots: list[str] = []
    seen: set[str] = set()
    boundary = resolve_workspace_boundary()
    if boundary is not None:
        roots.append(str(boundary))
        seen.add(str(boundary))
    for key in _START_ENV_KEYS:
        value = os.environ.get(key, "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        roots.append(value)
    cwd = str(Path.cwd().resolve())
    if cwd not in seen:
        roots.append(cwd)
    return roots


def main() -> None:
    graph_path = resolve_graph_path()
    roots = resolve_workspace_roots()
    from graphify.serve import serve

    serve(graph_path)


if __name__ == "__main__":
    main()
