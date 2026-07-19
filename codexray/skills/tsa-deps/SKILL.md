---
name: tsa-deps
version: 2.0.0
description: |
  Dependency / import graph analysis. Answer "what does this file import",
  "what imports this module", "what's the project's import topology",
  "show me the sitemap" without reading every file's import block.

  Use when:
  - "What does file X depend on" / "what imports module Y"
  - "Is module Z a leaf or a hub in the import graph"
  - "Show me the project sitemap" (which files glue what together)
  - "Are there circular imports"
  - Planning a module extraction: who'd you break

  Replaces: grep-for-import-statements + manual graph walking
  (~5k tokens for non-trivial repos) with 1 MCP call (~500 tokens).
allowed-tools:
  - mcp__codexray__health
  - mcp__codexray__structure
  - Bash
  - Read
---

# tsa-deps — Imports & module topology

## Tool routing

| Question                                | Tool                              |
|-----------------------------------------|-----------------------------------|
| One file's direct deps                  | `health action=deps`              |
| Project-wide import graph (who imports whom) | `health action=imports`      |
| Project topology (entry points, hubs)   | `structure action=sitemap`        |

## Procedure

### File-level deps

```yaml
health action=deps file_path="codexray/ast_cache.py" mode="file_deps"
# returns: {imports: [...], imported_by: [...], depth: 2}
```

`mode` options:
- `summary` — project-wide dependency summary (alias: `full`)
- `file_deps` — one file's graph (requires `file_path`)
- `blast_radius` — impact set for a file (alias: `blast`; requires `file_path`)
- `cycles` — circular dependencies

### Import graph (project-level)

```yaml
health action=imports language="python" limit=50
# returns: ranked list of import hubs + leaves
```

Use to find:
- **Hubs** (many things import this) — high blast radius if changed
- **Leaves** (no one imports this) — possibly dead, or a CLI entry point
- **Cycles** — circular imports needing breaking

### Sitemap

```yaml
structure action=sitemap
# returns: {entry_points: [...], hub_modules: [...], leaf_modules: [...]}
```

Useful as a "first look" right after `tsa-landing`.

## CLI equivalents

```bash
uv run codexray <file> --dependencies file_deps
uv run codexray --dependencies summary
uv run codexray --import-graph --import-graph-mode summary
uv run codexray --codegraph-sitemap
```

## Anti-patterns

- DON'T grep for `^import` / `^from` to build a graph — incomplete (misses
  conditional / lazy imports captured by the AST)
- DON'T worry about leaves at the start — they're often legitimate (CLI mains,
  examples). Focus on hubs.
- DON'T extract a hub module without first checking its `imported_by` list
  — you'll break dozens of callers.
