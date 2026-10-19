"""Tests for graphify.mcp_serve graph path resolution."""
from __future__ import annotations

import sys
from pathlib import Path

from graphify.mcp_serve import (
    expected_graph_path,
    find_graph_json,
    resolve_graph_path,
    resolve_workspace_boundary,
)


def test_find_graph_json_walks_upward_within_boundary(tmp_path):
    project = tmp_path / "apps" / "demo"
    graph = project / "graphify-out" / "graph.json"
    graph.parent.mkdir(parents=True)
    graph.write_text("{}", encoding="utf-8")

    assert find_graph_json(project / "src", stop_at=project) == graph.resolve()
    assert find_graph_json(project / "src", stop_at=project / "src") is None


def test_find_graph_json_does_not_escape_workspace_boundary(tmp_path):
    monorepo = tmp_path / "MCP"
    parent_graph = monorepo / "graphify-out" / "graph.json"
    parent_graph.parent.mkdir(parents=True)
    parent_graph.write_text('{"parent": true}', encoding="utf-8")

    workspace = monorepo / "agent-browser-use"
    workspace.mkdir()

    assert find_graph_json(workspace, stop_at=workspace) is None


def test_resolve_graph_path_uses_graphify_graph_env(tmp_path, monkeypatch):
    graph = tmp_path / "custom" / "graph.json"
    graph.parent.mkdir(parents=True)
    graph.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("GRAPHIFY_GRAPH", str(graph))
    monkeypatch.delenv("CURSOR_PROJECT_DIR", raising=False)
    assert resolve_graph_path() == str(graph)


def test_resolve_graph_path_scoped_to_workspace(tmp_path, monkeypatch):
    monorepo = tmp_path / "MCP"
    parent_graph = monorepo / "graphify-out" / "graph.json"
    parent_graph.parent.mkdir(parents=True)
    parent_graph.write_text("{}", encoding="utf-8")

    workspace = monorepo / "agent-browser-use"
    workspace.mkdir()

    monkeypatch.delenv("GRAPHIFY_GRAPH", raising=False)
    monkeypatch.setenv("CURSOR_PROJECT_DIR", str(workspace))
    monkeypatch.setenv("WORKSPACE_FOLDER", str(workspace))

    assert resolve_graph_path() == str(expected_graph_path(workspace))
    assert resolve_graph_path() != str(parent_graph.resolve())


def test_resolve_graph_path_uses_local_workspace_graph(tmp_path, monkeypatch):
    workspace = tmp_path / "agent-browser-use"
    graph = workspace / "graphify-out" / "graph.json"
    graph.parent.mkdir(parents=True)
    graph.write_text("{}", encoding="utf-8")

    monkeypatch.delenv("GRAPHIFY_GRAPH", raising=False)
    monkeypatch.setenv("CURSOR_PROJECT_DIR", str(workspace / "src"))
    monkeypatch.setenv("WORKSPACE_FOLDER", str(workspace))

    assert resolve_graph_path() == str(graph.resolve())


def test_resolve_workspace_boundary_prefers_workspace_folder(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    sub = root / "pkg"
    sub.mkdir(parents=True)
    monkeypatch.setenv("WORKSPACE_FOLDER", str(root))
    monkeypatch.setenv("CURSOR_PROJECT_DIR", str(sub))
    assert resolve_workspace_boundary() == root.resolve()


def test_mcp_serve_starts_without_graph(tmp_path, monkeypatch):
    """MCP server must stay up when graph.json is missing (multi-project mode)."""
    import os
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(repo_root), env.get("PYTHONPATH", "")])
    env.pop("GRAPHIFY_GRAPH", None)
    env["CURSOR_PROJECT_DIR"] = str(tmp_path)
    env["WORKSPACE_FOLDER"] = str(tmp_path)

    proc = subprocess.run(
        [sys.executable, "-m", "graphify.mcp_serve"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
    )
    assert "No module named graphify.mcp_serve" not in proc.stderr
    assert proc.returncode != 1 or "Graph file not found" not in proc.stderr
