# How CodeXray compares to CodeGraph

> Moved out of the README to keep it lean. Back to the [README](../README.md).

### Call-graph correctness — TSA resolves what CodeGraph mis-wires

Token cost is one axis; a code-intelligence tool's *first* job is a **correct graph**.

**Head-to-head on this repo, both tools' live indexes** (count every call edge whose caller language differs from the callee's — a cross-language mis-wire by construction; [reproducible](benchmarks/codegraph_compare/REPORT-v1.21.0.md)):

| tool | cross-language mis-wires | total call edges | rate |
|---|---|---|---|
| CodeGraph | **745** | 38,103 | 1.96 % |
| **CodeXray** | **6** | 114,160 | **0.005 %** |

**~390× cleaner on cross-language correctness, while resolving 3× more call edges.** CodeGraph's mis-wires span 19+ language pairs (python→swift **408**, python→typescript 195, python→ruby 81, …); TSA's 6 are all `java→python/php` from single-word Java method names.

> **Don't trust this table — run it on your own repo (no CodeGraph install needed):**
> ```bash
> uvx --from codexray-cli miswire-audit .
> ```
> It indexes your code and prints how many call edges a name-only resolver (the design most indexes use) *would* mis-wire across a language boundary vs how many TSA does — with the offending edges listed (`Python sorted() → Swift func at file:line`). Add `--card` for a shareable scorecard.
>
> **Real runs:** on [HuggingFace `tokenizers`](benchmarks/codegraph_compare/MISWIRE-AUDIT-EXAMPLES.md) (Rust+Python+JS+TS) a name-only resolver would mis-wire **1,259** call edges (incl. a JS `tokenize()` → Rust def) — TSA: **0**. On a single-language repo (`gin`, Go) both are **0** — no false positives. [More examples →](benchmarks/codegraph_compare/MISWIRE-AUDIT-EXAMPLES.md)

Concretely:

| call (Python `_resolve_entry_points` / `build_response`) | CodeGraph | TSA |
|---|---|---|
| `sorted()` (Python builtin) | ❌ callee = **`tests/golden/corpus_swift.swift` — a Swift `func sorted`** (wired as a callee of **299** Python functions repo-wide) | ✅ `builtin` — no cross-language edge |
| `fts_search()` / `fts_search_ranked()` | ❌ bound to the **test mock** (`FallbackCache`) instead of the real method | ✅ resolves to the source method (`_ast_cache_query.py` / `ast_cache.py`) |

TSA's per-language resolver gates every binding by **language family** across **13 languages** (Python · Java · Go · JS · TS · C · C++ · Rust · C# · Kotlin · Ruby · PHP · Swift) and **demotes test-only definitions** for non-test callers, across all of its resolution paths. Telling an agent that a Python function *calls a Swift method*, or that a production call targets a test mock, is wrong structural data — and it is the dominant failure mode of a name-only index.

#### Correct *and* complete — 96.3% of call edges classified

A correct graph that leaves most edges `unknown` is still half a graph. TSA's resolution cascade now classifies **96.3%** of call edges (up from 83.9%), with **zero** cross-language or test-shadow mis-wires — every gain is gated on the project owning no compatible-language symbol of that name, so shadowing is always preserved:

| resolver tier | what it resolves | source |
|---|---|---|
| binding cascade | local / self / import / unique-method / single-global | RFC-0002 |
| stdlib **method** names (`write_text`, `strip`, `items`) | `str` / `Path` / `dict` / `re` / `argparse` methods → `stdlib` | [RFC-0004](rfcs/0004-stdlib-method-resolution.md) |
| external **library** methods (`raises`, `given`, `MagicMock`) | pytest / hypothesis / mock → `external` | [RFC-0005](rfcs/0005-external-method-resolution.md) |

The remaining ~4% `unknown` is dominated by genuinely-unresolvable dynamic dispatch (`BaseTool.execute()`), constructors, and ambiguous same-name project methods — the false-positive floor of static analysis, left honest rather than guessed.

> **Now multi-language.** Cross-language-safe resolution is no longer Python-only. A per-language **resolver registry** ([RFC-0010](rfcs/0010-resolver-language-registry.md)) gives each language its own classification cascade with conservative stdlib/external tiers, gated by language family so a binding does not cross into an incompatible language. **Active classified call graph (call-edge extraction + per-language resolver), 13 languages: Python · Java · Go · JavaScript · TypeScript · C · C++ · Rust · C# · Kotlin · Ruby · PHP · Swift.** Each has its own conservative stdlib/external tiers and is adversarially verified to never bind across a language boundary. **Swift is notable**: CodeGraph's flagship mis-wire binds 299 Python `sorted()` callers to a Swift `func sorted` — TSA resolves Swift correctly *and* refuses that exact cross-language bind (verified both directions). Measured on the active set: **6** cross-language edges (6 of ~57,000 resolved edges, all generic 1-word Java method names) — **~390× cleaner than CodeGraph** on cross-language correctness, which wires **299** Python `sorted()` callers to a single Swift `func sorted` (TSA binds **0** of 298). Full reproducible audit: [`benchmarks/codegraph_compare/REPORT-v1.21.0.md`](benchmarks/codegraph_compare/REPORT-v1.21.0.md). Adding a language is one new resolver file (RFC-0010) plus a small call-extraction wiring.

> **Symbol kinds, too.** TSA classifies class members as `kind=method` (20,348 method rows on this repo) — `search action=symbol kind=method` returns them; CodeGraph parity, not a stub. The `index status` payload breaks symbols down by kind and language and edges by kind (`edges_by_kind` — a breakdown CodeGraph does not surface).

### Where TSA leads

- **Index build speed.** Removing a redundant post-index edge-refresh pass cut a cold django index (~2 950 files) from **181 s → 97 s (−46 %)**; the win grows with repo size. Re-index of unchanged files is a content-hash lookup.
- **Strict CLI superset.** Every MCP tool has a CLI equivalent (CodeGraph's CLI is thinner); *behavioural* defaults (ranking, limits, truncation) are kept in lock-step between the two surfaces. Output format is the one intentional divergence — MCP defaults to TOON (token-efficient for agents), the CLI to JSON (human/`jq`-friendly).
- **One-call expressiveness.** A jQuery-style chain DSL — `search('X').callees(depth=2).explore(include_code=true).answer(compact=true)` — returns an entire flow's subgraph + source in a single call, with JS-style `true`/`false` so agents can write it naturally.
- **Output is structured + token-aware.** TOON default for MCP (~half the size of JSON on bulk/tabular output; decision-tool wiring corrected in RFC-0018), per-call truncation hints, consistent test-file de-prioritisation across every ranking path.
- **Breadth.** Health scoring, safe-to-edit / change-impact gating, 13 curated Skills, and broad language coverage.

### On token cost — and a benchmark we corrected

> **Correction (2026-06).** An earlier version of this section claimed TSA beat CodeGraph on agent token cost (a "−11 % median" table). That benchmark had a harness bug: the TSA arm's MCP server was started without an explicit project root and analysed *codexray's own source* instead of the target repo, so its numbers were meaningless. The bug is fixed (the harness now passes `--project-root`), the inflated claim is withdrawn, and the honest picture is below.

Token cost was the one axis where CodeGraph led. [RFC-0006](rfcs/0006-context-progressive-disclosure.md) progressive disclosure closes most of the gap at the source: `nav context` now returns a **lean default** — entry points + a compact `related_symbols` list + code blocks — and moves the flat node/edge graph behind an opt-in `include_graph=true`. Measured on this repo (4 representative queries, TOON):

| context payload | chars |
|---|---|
| TSA default, before RFC-0006 | ~13,900 |
| **TSA default, after (lean)** | **~6,600 (−53%)** |
| TSA `include_graph=true` (full, opt-in) | ~13,900 |
| CodeGraph baseline | ~4,400 |

The dominant context call went from **~2.9× CodeGraph's payload to ~1.5×**.

For context, the per-task `$` cost measured **before** RFC-0006 (corrected harness — Claude Sonnet, gin + django, MCP arms, no errors):

| arm | median cost (pre-RFC-0006) | tool calls | file reads |
|---|---|---|---|
| CodeGraph MCP | **~$0.27** | 7 | 2 |
| CodeXray MCP | ~$0.44 | 7 | 1 |
| no-MCP (grep/read) | ~$0.34 | 14 | 7 |

A full per-task `$` re-benchmark is the next measurement (harness command below). We report the payload proxy straight rather than restate the old table as if RFC-0006 hadn't shipped.

### Reactive push + edge-kind breakdown — two things CodeGraph can't do

CodeGraph (and most one-shot indexers) only answer on poll: you ask, it replies with a snapshot, and you re-ask to learn whether anything changed. TSA exposes two capabilities that close that loop:

- **Reactive push / subscription ([RFC-0001](rfcs/0001-reactive-push.md), implemented).** `search action=subscribe` registers a Hyphae selector and returns a `tsa://hyphae/{selector}` MCP resource URI. When the watched code changes, the server emits a resource-updated notification — the agent re-reads the resource instead of polling. `search action=unsubscribe` cancels it. CodeGraph has no push or subscription channel.
- **`edges_by_kind` in `index action=status`.** Status returns a per-edge-kind count (calls / extends / implements / imports …), not just a single `total_edges` — so an agent can read the graph's shape (how call-heavy vs inheritance-heavy a repo is) before drilling in. CodeGraph surfaces only a flat total.

Reproduce the correctness fixes on any repo both tools have indexed:

```bash
# CodeGraph: emits the cross-language / test-shadow callee
#   (e.g. `sorted` → corpus_swift.swift, `fts_search` → test mock)
# TSA after the resolver fix: language-correct, source-preferring
codexray --callees _resolve_entry_points --format json
```

> Reproduce the cost numbers: `uv run python benchmarks/codegraph_compare/run.py phase full-warm --repos gin,django`. Raw envelopes + the harness fix live in that directory.
