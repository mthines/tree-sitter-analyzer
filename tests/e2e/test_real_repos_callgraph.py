"""End-to-end call-graph checks against four real open-source repositories.

These lock in the fork's call-graph behaviour on real, idiomatic code across
three languages, so regressions are caught consistently later:

- **Hono** (TypeScript, arrow-heavy) — arrow-const + class-field arrow +
  ``#private`` method resolution. Upstream reported ``fetch`` → 0 callees.
- **NestJS** (TypeScript, class/decorator) — the ambiguous-method-fanout gate.
  Upstream fanned a single ``loadInstance`` ``.get()`` out to ~17 unrelated
  ``get`` methods.
- **Flask** (Python) — class/method call resolution.
- **gin** (Go) — receiver-typed method call resolution.

Plus one check that the global extraction cache reuses work on a real repo.

Opt-in: marked ``e2e`` + ``network`` (excluded from the default suite). Run with::

    uv run pytest tests/e2e/test_real_repos_callgraph.py -m network -o addopts=""

Repos are shallow-cloned at their latest ``main`` via ``clone_repo_factory``;
assertions are deliberately structural (not exact edge counts) so normal
upstream evolution does not cause false failures. If an anchor function is not
found (upstream refactor), the test skips rather than fails. For fully pinned
runs, pre-clone at a fixed SHA and point ``E2E_REAL_REPO_<NAME>`` at the dir.

Behaviour last verified against: hono cadff88, nest 7cdb8f4, flask 36e4a82,
gin 34dac20.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

import tree_sitter_analyzer.call_graph as cg_mod
from tree_sitter_analyzer.call_graph import CallGraph

pytestmark = [pytest.mark.e2e, pytest.mark.network]

_HONO = ("https://github.com/honojs/hono.git", "hono")
_NEST = ("https://github.com/nestjs/nest.git", "nest")
_FLASK = ("https://github.com/pallets/flask.git", "flask")
_GIN = ("https://github.com/gin-gonic/gin.git", "gin")


def _build(repo_dir: Path, subdir: str | None = None) -> CallGraph:
    """Build a call graph rooted at ``repo_dir`` (optionally a subdirectory)."""
    root = repo_dir if subdir is None else repo_dir / subdir
    if not root.is_dir():
        pytest.skip(f"expected path missing (upstream layout changed): {root}")
    graph = CallGraph(str(root))
    graph.build()
    return graph


def _callees_or_skip(graph: CallGraph, func: str) -> list[str]:
    """Callee names of ``func``, or skip if ``func`` is not indexed at all."""
    if func not in {f["name"] for f in graph.all_functions()}:
        pytest.skip(f"{func!r} not found in indexed functions (upstream refactor)")
    return [c["name"] for c in graph.callees_of(func)]


def test_hono_arrow_and_private_method_resolution(clone_repo_factory) -> None:
    """A class-field arrow method resolves its ``this.#private()`` call — the
    exact arrow-const + ``#private`` case upstream dropped (``fetch`` → 0)."""
    repo = clone_repo_factory(*_HONO)
    graph = _build(repo, "src")

    callees = _callees_or_skip(graph, "fetch")
    assert "#dispatch" in callees, (
        "Hono `fetch` should resolve its `this.#dispatch()` call; "
        f"got callees={sorted(set(callees))}"
    )


def test_nestjs_qualified_method_call_does_not_fan_out(clone_repo_factory) -> None:
    """``loadInstance`` resolves real callees but its ambiguous ``.get()`` does
    not fan out to every same-named method (the ambiguity gate)."""
    repo = clone_repo_factory(*_NEST)
    graph = _build(repo, "packages/core")

    callees = _callees_or_skip(graph, "loadInstance")
    get_targets = [name for name in callees if name == "get"]
    assert len(get_targets) <= 2, (
        "ambiguous `.get()` should not fan out to many same-named methods; "
        f"got {len(get_targets)} `get` targets"
    )
    assert callees, "loadInstance should still resolve some real callees"


def test_flask_python_method_resolution(clone_repo_factory) -> None:
    """Flask's request-lifecycle method resolves its downstream calls."""
    repo = clone_repo_factory(*_FLASK)
    graph = _build(repo)

    callees = _callees_or_skip(graph, "full_dispatch_request")
    assert "dispatch_request" in callees, (
        "full_dispatch_request should call dispatch_request; "
        f"got callees={sorted(set(callees))}"
    )


def test_gin_go_receiver_method_resolution(clone_repo_factory) -> None:
    """gin's Go request dispatcher resolves receiver-typed method calls."""
    repo = clone_repo_factory(*_GIN)
    graph = _build(repo)

    callees = _callees_or_skip(graph, "handleHTTPRequest")
    assert callees, (
        "handleHTTPRequest should resolve at least one callee (Go receiver "
        "method resolution)"
    )


def test_extraction_cache_reuses_work_on_a_real_repo(
    clone_repo_factory, tmp_path, monkeypatch
) -> None:
    """A warm build of a real repo re-parses nothing — the global content-
    addressed extraction cache is doing its job end-to-end."""
    monkeypatch.setenv("TSA_CACHE_DIR", str(tmp_path / "cache"))
    repo = clone_repo_factory(*_GIN)

    CallGraph(str(repo)).build()  # cold: populates the cache

    parses = {"n": 0}
    original: Callable = cg_mod.Parser.parse_file

    def spy(self, path, language):  # type: ignore[no-untyped-def]
        parses["n"] += 1
        return original(self, path, language)

    monkeypatch.setattr(cg_mod.Parser, "parse_file", spy)
    CallGraph(str(repo)).build()  # warm: should hit the cache for every file

    assert parses["n"] == 0, f"warm build re-parsed {parses['n']} file(s)"
