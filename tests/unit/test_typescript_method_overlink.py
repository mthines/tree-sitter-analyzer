"""Ambiguity gate for unresolved qualified method calls in TypeScript/JS.

When a method is invoked on a receiver whose type is not statically known
(``reg.get(...)``) and the base name matches several unrelated definitions
across the project, the resolver must not fan the single call site out to
*every* same-named method — that is the NestJS ``loadInstance`` -> 17 ``get``
targets over-linking. Without receiver-type inference the correct answer is
"don't guess": emit no edge rather than a wrong one, matching the resolver's
own conservative philosophy and the accuracy seen on Go/Python.

Guards ensure the gate does not over-correct: a single project-wide candidate
still resolves, and unqualified module-level calls are untouched.

Tests exercise the public ``CallGraph`` API only.
"""

from __future__ import annotations

import textwrap

from codexray.call_graph import CallGraph


def _callee_names(cg: CallGraph, func: str) -> list[str]:
    return [c["name"] for c in cg.callees_of(func)]


def _write(tmp_path, name: str, body: str) -> None:
    (tmp_path / name).write_text(textwrap.dedent(body))


def test_ambiguous_qualified_method_call_does_not_fan_out(tmp_path):
    """``reg.get()`` with an unknown receiver type and three project-wide
    ``get`` definitions resolves to none of them, not all three."""
    _write(tmp_path, "cache.ts", "export class Cache { get(k: string) { return k } }\n")
    _write(tmp_path, "store.ts", "export class Store { get(k: string) { return k } }\n")
    _write(tmp_path, "config.ts", "export class Config { get(k: string) { return k } }\n")
    _write(
        tmp_path,
        "loader.ts",
        """\
        export class Loader {
          run(reg: any) {
            return reg.get('token')
          }
        }
        """,
    )
    cg = CallGraph(str(tmp_path))
    cg.build()

    assert _callee_names(cg, "run").count("get") == 0


def test_single_candidate_qualified_method_call_still_resolves(tmp_path):
    """The gate must not over-correct: one project-wide ``get`` keeps its edge."""
    _write(tmp_path, "cache.ts", "export class Cache { get(k: string) { return k } }\n")
    _write(
        tmp_path,
        "loader.ts",
        """\
        export class Loader {
          run(reg: any) {
            return reg.get('token')
          }
        }
        """,
    )
    cg = CallGraph(str(tmp_path))
    cg.build()

    assert "get" in _callee_names(cg, "run")


def test_unqualified_module_function_call_is_untouched(tmp_path):
    """A bare ``helper()`` call (no receiver) still resolves even when the
    global fallback is the resolving tier — the gate only guards qualified
    method calls."""
    _write(
        tmp_path,
        "util.ts",
        "export const helper = (x: number): number => x * 2\n",
    )
    _write(
        tmp_path,
        "app.ts",
        """\
        import { helper } from './util'

        export function compute(x: number): number {
          return helper(x) + 1
        }
        """,
    )
    cg = CallGraph(str(tmp_path))
    cg.build()

    assert "helper" in _callee_names(cg, "compute")
