# 🌳 CodeXray

**English** | **[日本語](README_ja.md)** | **[简体中文](README_zh.md)**

[![PyPI (upstream)](https://img.shields.io/pypi/v/tree-sitter-analyzer.svg)](https://pypi.org/project/tree-sitter-analyzer/) [![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org) [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![Stars](https://img.shields.io/github/stars/mthines/codexray.svg?style=social)](https://github.com/mthines/codexray) [![Works with Claude Code · Cursor · MCP](https://img.shields.io/badge/works%20with-Claude%20Code%20%C2%B7%20Cursor%20%C2%B7%20MCP-6f42c1.svg)](#supported-agents)

> **Fork.** [`mthines/codexray`](https://github.com/mthines/codexray) (CodeXray) is a fork of [`aimasteracc/tree-sitter-analyzer`](https://github.com/aimasteracc/tree-sitter-analyzer) (© its authors, MIT) — a shorter, more memorable name and a CLI-first (JSON + `jq`) workflow, plus stronger TypeScript/JavaScript call-graph resolution and a global extraction cache. See [What this fork adds](#what-this-fork-adds).

**Code intelligence AI agents can trust** — correct cross-language structure across 20+ languages, agent-native (MCP + CLI).

TSA indexes your codebase with tree-sitter and serves correct call graphs, symbol search, and structural queries to AI coding agents — locally, with no telemetry.

**Why it's different:**
* **Cross-language correctness is the moat.** A name-only index wires Python `sorted()` to a Swift `func sorted`. TSA doesn't. ~390× fewer cross-language call-graph mis-wires than alternatives ([reproducible audit](benchmarks/codegraph_compare/MISWIRE-AUDIT-EXAMPLES.md)).
* **Built agent-native.** 8 MCP tools, TOON output (~half the size of JSON on bulk/tabular responses), verdict envelopes, and 13 curated Skills — designed for Claude Code, Cursor, and any MCP client.
* **Broad and correctly classified.** 13 languages with full call-graph indexing (Python · Go · Rust · Java · JS · TS · C · C++ · C# · Swift · Kotlin · Ruby · PHP), 8 more symbol-indexed or CLI-reachable.

> **Proof:** on HuggingFace `tokenizers` (Rust+Python+JS+TS), a name-only resolver mis-wires **1,259** call edges — TSA: **0**. Run it on your repo in seconds: `uvx --from codexray-cli miswire-audit .`

> Upgrading from v1.x? See [docs/MIGRATION.md](docs/MIGRATION.md).

---

## What this fork adds

This fork extends upstream **v1.29.0** with call-graph improvements focused on modern TypeScript/JavaScript, plus a global build cache. Design notes: [`docs/design/global-extraction-cache.md`](docs/design/global-extraction-cache.md).

- **TypeScript / JavaScript call-graph correctness.** Arrow-const exports (`export const f = () => …`), class-field arrow methods (`fetch = () => …`), and `#private` methods are now registered as call-graph nodes. Upstream dropped their call edges, so an endpoint handler written in idiomatic arrow style reported *zero* callees. On the [Hono](https://github.com/honojs/hono) codebase: `fetch` callees **0 → 1**, call-graph edges-per-node **0.84 → 3.0**.
- **No same-name method fan-out.** A qualified call on a receiver whose type isn't statically known (`registry.get(...)`) no longer binds to *every* same-named method in the project. Without receiver-type inference the resolver stays conservative and emits no edge rather than a wrong one. On [NestJS](https://github.com/nestjs/nest): a single `loadInstance` `.get()` that fanned out to **17** unrelated methods → **0** false edges.
- **Global content-addressed extraction cache.** Per-file parse + extraction is memoised in a global, content-addressed store, so repeat runs and monorepo / nested invocations reuse work instead of re-parsing. **~5.5×** faster warm runs on a 350-file project. The key is `content + language + extractor version + installed grammar versions`, so a `tree-sitter` grammar upgrade can never serve stale results. Configure the location with `TSA_CACHE_DIR`; disable entirely with `TSA_DISABLE_GRAPH_CACHE=1`.

---

## Call graph for agents (CLI + jq)

The call graph is built to be driven straight from the CLI — no MCP server needed for shell-capable agents.
Point at the repo root, filter to one function, emit JSON, and narrow with `jq`.

```bash
# What FN calls, transitively — the execution map under an entry point
codexray --project-root . --call-graph chain \
  --call-graph-function FN --call-graph-depth 3 --format json

# Direct callees / callers of FN
codexray --project-root . --call-graph callees --call-graph-function FN --format json
codexray --project-root . --call-graph callers --call-graph-function FN --format json

# Disambiguate a common name by file
codexray --project-root . --call-graph callees \
  --call-graph-function FN --call-graph-file src/foo.ts --format json

# Whole-graph node/edge counts
codexray --project-root . --call-graph summary --format json
```

Keep only what you need with `jq` — it filters in the shell, so only the slice reaches the model's context:

```bash
# what FN calls — direct callee names
... --call-graph callees --call-graph-function FN --format json | jq -r '.callees[].name'

# callee name + location
... --call-graph callees --call-graph-function FN --format json \
  | jq -r '.callees[] | .name+"  "+.file+":"+(.line|tostring)'

# who calls FN
... --call-graph callers --call-graph-function FN --format json | jq -r '.callers[].name'

# transitive chain, first level only
... --call-graph chain --call-graph-function FN --format json \
  | jq -r '.chain[] | select(.depth==1) | .callee.name'

# transitive chain, unique callees at any depth
... --call-graph chain --call-graph-function FN --call-graph-depth 4 --format json \
  | jq -r '[.chain[].callee.name] | unique[]'

# how many edges were found
... --call-graph chain --call-graph-function FN --format json | jq '.edge_count'
```

Use `--format json` for `jq`; use `--format toon` (≈ half the size) when feeding a whole, small result straight to a model.

### JSON shape (stable contract)

`jq` recipes rely on these keys — treat them as a contract.

`--call-graph callees` / `callers`:

```json
{
  "mode": "callees",
  "function": "FN",
  "function_indexed": true,
  "callee_count": 9,
  "callees": [
    { "name": "cleanPath", "file": "path.go", "line": 23, "end_line": 124, "language": "go" }
  ]
}
```

`callers` is identical, with `caller_count` and `callers`.

`--call-graph chain`:

```json
{
  "mode": "chain",
  "function": "FN",
  "depth": 3,
  "edge_count": 38,
  "chain": [
    {
      "caller": { "name": "handleHTTPRequest", "file": "gin.go", "line": 690, "end_line": 760, "language": "go", "receiver": "Engine" },
      "callee": { "name": "cleanPath", "file": "path.go", "line": 23, "end_line": 124, "language": "go" },
      "depth": 1
    }
  ]
}
```

`receiver` is present on method calls (the type the method belongs to) and absent on free functions.

`--call-graph summary`:

```json
{ "mode": "summary", "function_count": 1323, "call_edge_count": 3202, "file_count": 96 }
```

> **Empty results are honest, not silent.** `function_indexed: false` or `callee_count: 0` means the tool could not resolve that function — never read it as "calls nothing." Trace those by hand; the graph is static structure, not a runtime path.

---

## Get Started

> **Requires Python 3.10+** (check: `python3 --version`). Install from [python.org](https://www.python.org/downloads/) if needed.

### Install

```bash
# run on demand with uvx
uvx --from "codexray-cli[all,mcp]" codexray --help

# or install into an environment (all languages + MCP)
pip install "codexray-cli[all,mcp]"
```

> Want the latest unreleased changes? Install from git instead:
> `pip install "codexray-cli[all,mcp] @ git+https://github.com/mthines/codexray.git"`

### Automated install

```bash
curl -fsSL https://raw.githubusercontent.com/mthines/codexray/main/install.sh | bash
```

Auto-installs `uv` if missing, detects Claude Desktop / Claude Code / Cursor / VS Code, and writes the MCP entry. Run `codexray --doctor` to verify.
One-line install for **Claude Code**:

```bash
claude mcp add codexray \
  --env TREE_SITTER_PROJECT_ROOT="$PWD" \
  -- uvx --from "codexray-cli[mcp]" codexray-mcp
```

Restart your agent, then say: *"Run the `index` tool with action=status."*
CLI equivalent (no agent needed): `codexray --codegraph-status`

> **PyPI / uvx users — install skills:** the 13 `tsa-*` skills are bundled in the wheel. Copy them once with:
> ```bash
> codexray --install-skills              # into ./.claude/skills/ (this project)
> codexray --install-skills-global       # into ~/.claude/skills/ (all projects)
> ```
> Git-clone users already have them under `.claude/skills/` — no action needed.

[Other agents (Cursor, Copilot, Cline, Continue, Claude Desktop, Roo Code) →](#supported-agents)

### Quick install

#### 1. Install dependencies

```bash
# uv (required)
curl -LsSf https://astral.sh/uv/install.sh | sh        # macOS / Linux
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# fd + ripgrep (required for `search action=content` text search; symbol search uses SQLite FTS5 and needs neither)
brew install fd ripgrep                                # macOS
winget install sharkdp.fd BurntSushi.ripgrep.MSVC      # Windows
```

#### 2. Install CodeXray

```bash
# Standalone install (persistent CLI command):
uv tool install "codexray-cli[all,mcp]"
# — or skip installing entirely: the MCP entry below runs via uvx on demand.
# Inside a uv-managed Python project, use: uv add "codexray-cli[all,mcp]"
```

#### 3. Hook it into your agent

See **[Supported Agents](#supported-agents)**. Most clients want this MCP server entry:

```json
{
  "mcpServers": {
    "codexray": {
      "command": "uvx",
      "args": ["--from", "codexray-cli[mcp]", "codexray-mcp"],
      "env": { "TREE_SITTER_PROJECT_ROOT": "/absolute/path/to/your/project" }
    }
  }
}
```

After restart: *"Run the `index` tool with action=status."*
CLI equivalent (no agent needed): `codexray --codegraph-status`

**See the correctness edge on your own repo** — no install, no CodeGraph (it re-indexes first; seconds on a small repo, a minute or two on a large one):

```bash
uvx --from codexray-cli miswire-audit .
```

It prints how many call edges a name-only code index (the design most tools use) *would* mis-wire across a language boundary — e.g. a Python `sorted()` wired to a Swift `func sorted` — versus how many TSA does (≈0). On [HuggingFace `tokenizers`](benchmarks/codegraph_compare/MISWIRE-AUDIT-EXAMPLES.md): **1,259 → 0**.

---

## Why CodeXray

* **Token-efficient on bulk output.** Every MCP response uses **TOON**, a tabular JSON variant that cuts **bulk/tabular** payloads by roughly half vs raw JSON ([measured invariant](tests/unit/mcp/test_output_cost_invariants.py)). Note: small metadata-heavy *decision-tool* responses are currently ~equal-to-larger than JSON under the present envelope wiring — tracked by a strict-xfail invariant and being corrected in [RFC-0018](rfcs/0018-response-envelope-normalization-and-adaptive-toon.md).
* **Verdict envelopes.** Every response carries `verdict: SAFE | CAUTION | UNSAFE | INFO | REVIEW | WARN | ERROR | NOT_FOUND`, so orchestrators branch on outcomes without re-prompting.
* **Project health grading (A–F).** Few code-intel tools expose a whole-project quality grade — TSA grades on size / complexity / coverage / duplication / dependencies / structure / git-hotspots in one call.
* **13 curated workflows (Skills).** Pre-baked tool subsets for "find symbol", "trace call chain", "score health", "safe-to-edit before refactor", "PR review", etc.
* **5 layers of safety.** `edit action=safe` + `edit action=guard` + constraint DSL + `edit action=impact` + verdict envelopes — designed so agents *know* before they touch.
* **Strict CLI superset of CodeGraph, faster indexing, and a one-call query DSL** — with an honest cost comparison ([below](#how-tsa-compares-to-codegraph)).

---

## Key Features

### Pre-indexed code intelligence (CodeGraph parity + superset)

| Capability | TSA tool | Status |
|---|---|---|
| Symbol search (FTS5 + **BM25 ranked**) | `search` action=symbol | **ahead** — results sorted by relevance score, not file path |
| Go-to-def / find-refs / call hierarchy in one call | `nav` action=navigate | PRIMARY entry point |
| Bulk-fetch N related symbols + relationship map | `structure` action=explore | parity |
| Function-level blast radius + risk score | `nav` action=impact | parity + risk score |
| Who-calls-X / what-X-calls | `nav` action=callers / action=callees | parity |
| Index health at-a-glance (+ edge count) | `index` action=status | **ahead** — reports `total_edges` for graph density signal |
| Pre-built call graph cache | `index` action=auto / action=full / action=sync | parity |
| Tests affected by a change (CLI) | `--affected FILE...` | parity |

### CodeXray exclusive

| Capability | TSA tool | Note |
|---|---|---|
| **BM25-ranked symbol search** | all search tools | relevance_score on every result (min-max normalized: best=1.0, weakest=0.0); sort(by='confidence') in DSL |
| **Semantic search (BM25 pre-filtered)** | `search` action=chain (`semantic()` DSL) | BM25 pre-filter narrows 40k symbols to ~400 before cosine rerank |
| **Project A–F health grading** | `health` action=project | 7 dimensions (size/complexity/deps/coverage/duplication/structure/git-hotspot), uncommon among code-intel tools |
| **TOON output** | every tool, `output_format: "toon"` (default) | ~50 % token saving on bulk/tabular output (decision tools tracked by RFC-0018) |
| **Verdict envelopes** | every tool | `SAFE/CAUTION/UNSAFE/INFO/WARN/ERROR/NOT_FOUND` |
| **Safe-to-edit gate** | `edit` action=safe / action=guard | refuses high-risk edits before they happen |
| **Architectural constraint DSL** | `edit` action=constraints | "module A cannot import B" → enforced |
| **Code health (file-level)** | `health` action=file | block/long-method/smell detection |
| **Class hierarchy** | `structure` action=class_tree | type-inheritance tree |
| **Dependency matrix** | `health` action=matrix | module-coupling matrix |
| **Dead code** | `health` action=dead | transitive unreachable analysis |
| **Complexity heatmap** | `health` action=heatmap | per-fn cyclomatic + project view |
| **AST-structural clone detection** | `viz` action=similarity | beyond text similarity |
| **Mermaid call-graph export** | `viz` action=graph | paste-ready in docs |
| **UML Mermaid export** | `viz` action=uml | class / package / component / sequence diagrams |
| **PR review** | `edit` action=pr | AST-diff + semantic classify + blast radius |
| **agent_summary** | every response | next-step hint baked into the envelope |
| **Synapse cross-file resolver** | internal | import-aware, beats regex guessing |
| **Temporal activation** | `nav` action=lineage | per-symbol git-modification frequency |
| **One-shot file orientation** | `project` action=smart | health + exports + deps + edit-risk in one call (replaces 3-4 calls) |
| **Architectural decision journal** | `project` action=journal | persists reasoning across sessions — uncommon among code-intel tools |

### Skills (13 curated workflows)

CodeGraph has zero skills. We ship 13 under `.claude/skills/tsa-*/`:

`tsa-landing`, `tsa-find`, `tsa-graph`, `tsa-structure`, `tsa-deps`, `tsa-index`, `tsa-health-watch`, `tsa-edit-safety`, `tsa-edit-then-verify`, `tsa-constraints`, `tsa-pr-review`, `tsa-refactor-queue`, `tsa-temporal`.

Each skill ships an `allowed-tools` subset + procedure recipe + decision-surface schema, so the agent doesn't have to triage 8 tools on every question.

### 321 CLI flags

Superset of CodeGraph's CLI surface. Highlights:

```bash
codexray --table full <file>          # method/signature/complexity table
codexray --partial-read --start-line N --end-line M <file>
codexray --project-health             # A-F grade across the project
# Note: --callers / --callees require the call-graph index — run --full-index first
codexray --full-index                 # build call-graph index (run once)
codexray --callers <symbol>           # who-calls
codexray --codegraph-impact <fn>      # blast radius + risk
codexray --affected <file...>         # tests transitively affected
codexray --dead-code                  # transitive unreachable
codexray --check-constraints          # architectural rules
codexray --safe-to-edit <file>        # refuse if risky
codexray --uml class                  # Mermaid UML class diagram
```

Installing the package also registers three standalone search utilities (thin
entry points over the same engine, handy in shell pipelines):

```bash
list-files <dir>          # fd-style file discovery
search-content <pattern>  # ripgrep-style content search
find-and-grep <pattern>   # two-stage fd + ripgrep
```

See [`docs/CODEMAPS/cli.md`](docs/CODEMAPS/cli.md) for the full surface.

---

## How TSA compares to CodeGraph

CodeXray is a **strict CLI superset of CodeGraph** with far cleaner cross-language call-graph resolution (~390× fewer cross-language mis-wires on this repo), faster indexing, reactive push, and an honest token-cost comparison. Full head-to-head numbers, the resolver cascade, and the reproducible audit live in **[docs/comparison-vs-codegraph.md](docs/comparison-vs-codegraph.md)**.

Run it on your own repo (no CodeGraph install needed): `uvx --from codexray-cli miswire-audit .`

---

## How It Works

```
Source code → tree-sitter parse → SQLite + FTS5 index (.ast-cache/index.db)
                                         ↓
        nav (navigate) / structure (explore) / nav (callers) / ...
                                         ↓
                            TOON-encoded envelope
                            (compact for tabular output;
                             verdict + agent_summary + data)
                                         ↓
                              MCP client / CLI consumer
```

The index is built lazily on first query, refreshed on file change via a content-hash diff (`index` action=sync). All 8 tools read from the same `.ast-cache/`, so a query and its follow-up share work.

---

## Supported Agents

CodeXray speaks MCP over stdio and works with Claude Code, Claude Desktop, Cursor, GitHub Copilot (VS Code), Cline, Continue, Roo Code, and Docker. The quickest start (Claude Code):

```bash
claude mcp add codexray \
  --env TREE_SITTER_PROJECT_ROOT="$PWD" \
  -- uvx --from "codexray-cli[mcp]" codexray-mcp
```

Per-client config (Claude Desktop, Cursor, Copilot, Docker, …) and the skills-install steps are in **[docs/mcp-client-setup.md](docs/mcp-client-setup.md)**.

> ⚠️ `TREE_SITTER_PROJECT_ROOT` must be **absolute** — the server enforces a security boundary via `SecurityValidator`.

---

## Supported Languages

22 language plugins; 13 fully wired into the indexer (full symbol + call graph) + 2 symbol-indexed (call-graph wiring pending) + 5 (data/markup) reachable via the single-file CLI path + 2 scaffold (plugin exists, indexer wiring pending). bash and scala graduated in v1.22.0; the 2026-05-24 patch unblocked Swift / Kotlin / Ruby / PHP / C# that had been silently skipped for months.

| Tier | Languages |
|---|---|
| **Full index + symbol + call graph** | Python · Java · JavaScript · TypeScript · Go · Rust · C · C++ · C# · Swift · Kotlin · Ruby · PHP |
| **Full index + symbols (call-graph wiring pending)** | Bash · Scala |
| **Single-file analysis (CLI)** | HTML · CSS · Markdown · SQL · YAML |
| **Scaffold (plugin exists, indexer wiring pending)** | JSON · Lua |

CodeGraph supports a similar set. **Dart, Vue, Svelte, Lua** are not yet shipped — aspirational backlog, no committed date.

---

## Configuration

Mostly nothing. The defaults are designed so you can hook it into your agent and forget:

* **Output format**: TOON. Override per-call with `output_format: "json"`.
* **Project root**: `TREE_SITTER_PROJECT_ROOT` (env var, MCP) or `--project-root` (CLI).
* **Cache location**: `<project>/.ast-cache/`. Safe to delete — auto-rebuilds.
* **Optional**: `TREE_SITTER_OUTPUT_PATH` for large-output write target.

---

## Quality & Testing

| Metric | Value |
|---|---|
| Tests passed | Comprehensive test suite ✅ |
| Type safety | 100 % mypy |
| Platforms | macOS · Linux · Windows |
| Pre-commit gates | ruff · bandit · mypy · pyupgrade · detect-secrets · tsa-codemap-sync |

```bash
uv run pytest -q                                # full suite
uv run pytest -q --maxfail=1 -m "not slow and not full_language and not integration"  # fast local loop
PYTEST_XDIST_AUTO_NUM_WORKERS=1 uv run pytest -q --maxfail=1 -m "not slow and not full_language and not integration"  # one-worker mode for lower CPU load
PYTEST_XDIST_AUTO_NUM_WORKERS=2 uv run pytest -q --maxfail=1 -m "not slow and not full_language and not integration"  # two-worker balanced mode
uv run pytest --lf --maxfail=1                  # rerun only failed tests from last run
uv run python check_quality.py --new-code-only  # quality gate
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unsupported language` on `.swift / .kt / .rb / .php / .cs` | Update to ≥ 1.12.x — the 5-language gap was patched in commit `50e99a8f`. Grammar modules for extras-gated languages are not bundled in the base install; run `pip install "codexray-cli[swift]"` (or `kotlin`, `ruby`, `php`, `csharp`) to add them. |
| MCP server doesn't appear in client | `TREE_SITTER_PROJECT_ROOT` must be an **absolute path** (e.g. `$(pwd)` or `/home/user/project`); a relative path causes the server to resolve against the wrong directory. Restart the client after editing. Run `codexray --doctor` to verify. |
| `database is locked` | Stop any other process holding `.ast-cache/index.db`; if persistent, `rm -rf .ast-cache && codexray --full-index`. |
| Slow first call | First call builds the index. Subsequent calls are sub-second. Run `--full-index` upfront to amortise. |
| Agent picks the wrong tool | Use a `tsa-*` skill (`/tsa-graph`, `/tsa-find`, ...) — each skill restricts the visible tool set to one workflow. |

---

## Development

```bash
git clone https://github.com/mthines/codexray.git
cd codexray
uv sync --extra all --extra mcp
uv run pytest -q
```

See **[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)** for the development guide.

---

## Contributing & License

* ⭐ A GitHub star helps surface this tool to other AI-agent users.
* 💖 [Sponsor](https://github.com/sponsors/aimasteracc) — supports continued MCP / Skills development.
* Lead sponsor: **[@o93](https://github.com/o93)**.
* MIT licensed — see [LICENSE](LICENSE).
* Release history: [CHANGELOG.md](CHANGELOG.md).
