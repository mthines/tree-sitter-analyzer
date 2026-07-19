"""Global content-addressed extraction cache for the call graph.

``CallGraph.build`` re-parses every file on every invocation. These tests pin
the caching behaviour: a warm cache skips re-parsing unchanged files (including
across different project roots, because the key is file *content*, not path),
a content change busts the entry, and results are byte-for-byte identical with
or without the cache. The cache is keyed under ``$TSA_CACHE_DIR`` so tests stay
hermetic.

Behaviour is observed through the public ``CallGraph`` API plus a parse counter;
no cache internals are imported.
"""

from __future__ import annotations

import tree_sitter_analyzer.call_graph as cg_mod
import tree_sitter_analyzer.graph_extraction_cache as gec_mod
from tree_sitter_analyzer.call_graph import CallGraph

_TWO_FUNCS = "export const a = () => 1\nexport const b = () => a()\n"


def _count_parses(monkeypatch) -> dict[str, int]:
    counter = {"n": 0}
    original = cg_mod.Parser.parse_file

    def spy(self, path, language):
        counter["n"] += 1
        return original(self, path, language)

    monkeypatch.setattr(cg_mod.Parser, "parse_file", spy)
    return counter


def _callees(cg: CallGraph, func: str) -> list[str]:
    return [c["name"] for c in cg.callees_of(func)]


def test_warm_cache_avoids_reparsing_unchanged_files(tmp_path, monkeypatch):
    monkeypatch.setenv("TSA_CACHE_DIR", str(tmp_path / "cache"))
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "app.ts").write_text(_TWO_FUNCS)

    CallGraph(str(proj)).build()  # cold: populates the cache

    counter = _count_parses(monkeypatch)
    CallGraph(str(proj)).build()  # warm: should hit the cache, no re-parse

    assert counter["n"] == 0


def test_results_are_identical_with_and_without_cache(tmp_path, monkeypatch):
    """The cache must never change the answer — only the speed."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "app.ts").write_text(_TWO_FUNCS)

    monkeypatch.setenv("TSA_DISABLE_GRAPH_CACHE", "1")
    cold = CallGraph(str(proj))
    cold.build()

    monkeypatch.delenv("TSA_DISABLE_GRAPH_CACHE")
    monkeypatch.setenv("TSA_CACHE_DIR", str(tmp_path / "cache"))
    cached = CallGraph(str(proj))
    cached.build()

    assert _callees(cached, "b") == _callees(cold, "b")


def test_content_change_busts_the_cache(tmp_path, monkeypatch):
    """Editing a file to same-name-different-body yields fresh edges, not stale."""
    monkeypatch.setenv("TSA_CACHE_DIR", str(tmp_path / "cache"))
    proj = tmp_path / "proj"
    proj.mkdir()
    app = proj / "app.ts"
    app.write_text("export const a = () => 1\nexport const b = () => 2\n")
    assert "a" not in _callees(CallGraph(str(proj)), "b")  # cold: b does not call a

    app.write_text("export const a = () => 1\nexport const b = () => a()\n")
    assert "a" in _callees(CallGraph(str(proj)), "b")  # warm cache must not go stale


def test_same_content_reused_across_project_roots(tmp_path, monkeypatch):
    """Content addressing: an identical file under a second root is not re-parsed
    — the monorepo / nested-invocation reuse case."""
    monkeypatch.setenv("TSA_CACHE_DIR", str(tmp_path / "cache"))
    root_a = tmp_path / "a"
    root_a.mkdir()
    (root_a / "shared.ts").write_text(_TWO_FUNCS)
    CallGraph(str(root_a)).build()  # populate cache from root A

    root_b = tmp_path / "b"
    root_b.mkdir()
    (root_b / "shared.ts").write_text(_TWO_FUNCS)  # byte-identical content
    counter = _count_parses(monkeypatch)
    CallGraph(str(root_b)).build()

    assert counter["n"] == 0


def test_grammar_version_change_busts_the_cache(tmp_path, monkeypatch):
    """A tree-sitter grammar upgrade must invalidate cached extraction, even
    though the file content is byte-identical — the grammar fingerprint is part
    of the key."""
    monkeypatch.setenv("TSA_CACHE_DIR", str(tmp_path / "cache"))
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "app.ts").write_text(_TWO_FUNCS)

    monkeypatch.setattr(gec_mod, "_grammar_fingerprint", lambda: "grammar-v1")
    CallGraph(str(proj)).build()  # populates the cache under the v1 fingerprint

    monkeypatch.setattr(gec_mod, "_grammar_fingerprint", lambda: "grammar-v2")
    counter = _count_parses(monkeypatch)
    CallGraph(str(proj)).build()  # different fingerprint -> miss -> re-parse

    assert counter["n"] == 1
