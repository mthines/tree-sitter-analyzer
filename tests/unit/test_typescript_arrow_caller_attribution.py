"""Call-edge attribution for idiomatic TypeScript function shapes.

Regression coverage for the arrow-heavy idioms that dominate modern TS/JS
codebases (arrow-const exports, class-field arrow methods, ``#private``
methods). Before this fix, calls made from the bodies of these functions were
dropped from the call graph because the enclosing function was never registered
as a node — ``callees_of`` returned an empty list for real request-dispatch
entry points (observed on the Hono codebase: ``fetch`` -> 0 callees).

Tests exercise the public ``CallGraph`` API only, so they survive an internal
refactor of the extraction pipeline.
"""

from __future__ import annotations

import textwrap

from codexray.call_graph import CallGraph


def _callee_names(cg: CallGraph, func: str) -> list[str]:
    return [c["name"] for c in cg.callees_of(func)]


def test_arrow_const_body_calls_are_attributed_to_it(tmp_path):
    """``export const compute = () => { helper() }`` records compute -> helper."""
    (tmp_path / "app.ts").write_text(
        textwrap.dedent(
            """\
            export const helper = (x: number): number => x * 2

            export const compute = (x: number): number => {
              return helper(x) + 1
            }
            """
        )
    )
    cg = CallGraph(str(tmp_path))
    cg.build()

    assert "helper" in _callee_names(cg, "compute")


def test_class_field_arrow_method_calls_are_attributed_to_it(tmp_path):
    """A class-field arrow method (``fetch = () => this.dispatch()``) is
    registered and its body call is attributed to it — the exact Hono
    ``fetch`` -> 0 callees case."""
    (tmp_path / "server.ts").write_text(
        textwrap.dedent(
            """\
            export class Server {
              fetch = (req: string): string => {
                return this.dispatch(req)
              }

              dispatch(req: string): string {
                return req
              }
            }
            """
        )
    )
    cg = CallGraph(str(tmp_path))
    cg.build()

    assert "dispatch" in _callee_names(cg, "fetch")


def test_private_method_body_calls_are_attributed_to_it(tmp_path):
    """A ``#private`` method's body call is attributed to it — the private
    name (``private_property_identifier``) must register as a node."""
    (tmp_path / "server.ts").write_text(
        textwrap.dedent(
            """\
            export class Server {
              #dispatch(req: string): string {
                return this.handle(req)
              }

              handle(req: string): string {
                return req
              }
            }
            """
        )
    )
    cg = CallGraph(str(tmp_path))
    cg.build()

    assert "handle" in _callee_names(cg, "#dispatch")
