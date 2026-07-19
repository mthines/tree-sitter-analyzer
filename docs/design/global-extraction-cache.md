# Design: Global content-addressed extraction cache

## Problem

`CallGraph.build()` re-parses **every** source file on every invocation. There is
no persistence between CLI runs, and each project root keeps its own state. In a
monorepo you pay the full parse cost again when you:

- run the same command twice (nothing changed), or
- run it at the monorepo root after running it on a sub-package (or vice-versa) —
  the shared files are re-parsed because caches are keyed by location, not content.

## Non-goal / the trap to avoid

Do **not** cache the *resolved* call graph of a directory and compose parents from
it. Call edges cross package boundaries (`packages/a` → `packages/b`), so a
subtree's resolved graph is not self-contained. Caching it is unsound.

## Key insight

`CallGraph.build()` is already two passes:

1. **Extraction** (`walk_tree` + `walk_imports`) — a pure function of a single
   file's bytes. Fully cacheable.
2. **Resolution** (wire call sites to definitions) — global, needs the whole
   symbol index, but cheap (index lookups, not parsing).

Parsing dominates cost. So: **cache extraction, always re-run resolution.**

## Design

### Content addressing

Cache key = `blake2b(file_bytes + language + EXTRACTOR_VERSION + grammar_fingerprint)`.
Because the key is the *content*, not the path, the same file hits the same entry
regardless of which root it was reached from — this is what delivers monorepo /
nested reuse for free. Renames and moves with identical content also hit.

Two version components guard correctness across upgrades:

- `EXTRACTOR_VERSION` — this project's extractor. Bump it when `walk_tree` /
  `walk_imports` output shape changes.
- `grammar_fingerprint` — a digest of the installed `tree-sitter*` package
  versions. The grammars are independently versioned deps with open ranges, so a
  `pip install -U` within range can change the parse tree with no code change
  here. Folding the versions in invalidates the cache automatically on any
  grammar upgrade (conservative: any grammar bump invalidates all languages).

Together they mean no stale parses after any upgrade — ours or a grammar's.

### Why not byte-size (the original idea)

Size alone collides: a same-length edit (swap two lines, change a constant to an
equal-length value) keeps the size identical while the code changed → stale, wrong
result. Content hashing is the source of truth. (Size + mtime is fine only as a
*fast-skip hint*, which the existing per-file `ast_cache` already uses.)

### Store layout (global)

```
$CODEXRAY_CACHE_DIR                 # explicit override (tests, CI)
  else $XDG_CACHE_HOME/codexray/graph-extract
  else ~/.cache/codexray/graph-extract
    objects/<aa>/<full-hash>.json     # sharded by first 2 hex chars
```

Each object is `{version, language, definitions, calls, imports}` as JSON.
Content-addressed objects are immutable, so writes are **write-temp + atomic
rename** — naturally safe for parallel invocations (monorepo CI) with no locking.

### Integration (`CallGraph.build`, pass 1)

```
bytes = read(abs_path)                       # cheap; needed for the hash anyway
hit   = cache.load(bytes, language)          # None on miss / disabled / error
if hit:
    definitions, calls, imports = hit        # no parse
else:
    tree = parser.parse_file(abs_path, language)
    definitions, calls = walk_tree(tree, ...)
    imports = walk_imports(tree, ...)
    cache.store(bytes, language, definitions, calls, imports)
```

Resolution (pass 2) is unchanged. The cache is **best-effort**: any I/O or
decode error falls back to a live parse — a broken cache can never fail a build
or return a wrong answer (the version-in-key guards correctness).

### Opt-out

`CODEXRAY_DISABLE_GRAPH_CACHE=1` disables read+write (live parse always). Correctness
is identical with or without the cache; only speed differs.

## Split into PRs

- **PR 3 (this):** the global content-addressed extraction cache above. Delivers
  repeat-run and monorepo/nested reuse in one slice.
- **PR 4 (deferred, optimization):** Merkle per-directory hashes to skip walking
  unchanged subtrees entirely (don't even `stat`). Only worth building once PR 3
  is measured — walking + hashing is already cheap (~10ms/1300 files), so this is
  a second-order win. Not built until numbers justify it (YAGNI).
```
