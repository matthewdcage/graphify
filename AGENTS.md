## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- When working on Graphify itself, use the repository's existing Graphify guidance. For codebase questions, prefer scoped graph queries where available; use the report for broad orientation. Do not use the graph as evidence when the task concerns the graph's correctness itself.
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)

## Project Overview

graphify is a Python CLI tool and AI coding assistant skill that converts any folder of code, docs, papers, images, or videos into a queryable knowledge graph with community detection.

**Pipeline:** `detect() → extract() → build_graph() → cluster() → analyze() → report() → export()`

Each stage is a single function in its own module. They communicate through plain Python dicts and NetworkX graphs — no shared state, no side effects outside `graphify-out/`.

## Key Modules

| Module | Responsibility |
|--------|---------------|
| `graphify/detect.py` | File discovery, type classification (code/doc/paper/image/video), `.graphifyignore` support |
| `graphify/extract.py` | AST extraction via tree-sitter for 25 languages + LLM extraction for docs/papers/images |
| `graphify/build.py` | Merges extraction dicts into a NetworkX graph |
| `graphify/cluster.py` | Leiden community detection via graspologic |
| `graphify/analyze.py` | God nodes, surprising connections, suggested questions |
| `graphify/report.py` | Renders GRAPH_REPORT.md from graph + analysis |
| `graphify/export.py` | Outputs graph.html (vis.js), graph.json, graph.svg, Obsidian vault, wiki, GraphML, Neo4j Cypher |
| `graphify/serve.py` | MCP stdio server exposing query_graph, get_node, get_neighbors, shortest_path, etc. |
| `graphify/mcp_serve.py` | Resolves `graphify-out/graph.json` from workspace context; entry point for Cursor MCP (`python -m graphify.mcp_serve`) |
| `graphify/llm.py` | Direct LLM backend for non-skill extraction (Claude, Kimi K2.6) |
| `graphify/cache.py` | SHA256-based semantic cache — re-runs only process changed files |
| `graphify/security.py` | URL validation, path traversal prevention, label sanitization |
| `graphify/validate.py` | Extraction schema validation |
| `graphify/watch.py` | File watcher for auto-rebuild on code changes |
| `graphify/ingest.py` | URL fetching (papers, tweets, videos) |
| `graphify/transcribe.py` | Video/audio transcription via faster-whisper |
| `graphify/wiki.py` | Wikipedia-style markdown wiki generation |
| `graphify/__main__.py` | CLI entry point, platform installers (Claude, Cursor, Codex, Gemini, etc.) |

## Confidence Labels

- **EXTRACTED** — relationship explicitly in source (import, call, citation)
- **INFERRED** — reasonable deduction with confidence_score (0.0–1.0)
- **AMBIGUOUS** — uncertain, flagged for human review

## Running Tests

```bash
pytest tests/ -q
```

All tests are pure unit tests — no network calls, no file system side effects outside `tmp_path`.

## MCP Server

graphify exposes its graph as an MCP stdio server for agent access.

**Direct serve** (fixed graph path):

```bash
python -m graphify.serve graphify-out/graph.json
```

**Cursor / workspace-aware serve** (scoped to the open workspace folder only; does not load a parent monorepo graph):

```bash
python -m graphify.mcp_serve
```

Tools exposed: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`.

## Cursor Integration

Run once per project (from the project root):

```bash
graphify cursor install          # global skill + .cursor/rules/graphify.mdc + .cursor/mcp.json entry
graphify cursor install --force  # refresh rule and MCP entry after upgrades
graphify build .                 # build code graph in terminal (AST only)
graphify .                       # shorthand for graphify build .
graphify cursor uninstall        # remove project rule and graphify MCP entry
```

`graphify cursor install` writes:

| Artifact | Purpose |
|----------|---------|
| `~/.claude/skills/graphify/SKILL.md` | Global `/graphify` skill (Cursor + Claude Code) |
| `~/.cursor/skills/graphify/SKILL.md` | Global `/graphify` skill (Cursor) |
| `.cursor/rules/graphify.mdc` | Always-on LLM hints when `graphify-out/` exists |
| `.cursor/mcp.json` → `mcpServers.graphify` | MCP entry using `python -m graphify.mcp_serve` |

Reload Cursor MCP servers after install. Existing unrelated MCP servers in `mcp.json` are preserved.

## Development Guidelines

- Code files are processed locally via tree-sitter AST — no LLM needed
- Docs/papers/images require LLM extraction (Claude subagents or direct API)
- Video/audio transcription runs locally with faster-whisper
- No telemetry, no analytics — only network calls are to model APIs during extraction
- All external input passes through `graphify/security.py` before use
- PyPI package name is `graphifyy` (double-y), CLI command is `graphify`
