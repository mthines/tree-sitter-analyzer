#!/usr/bin/env python3
"""Fast, index-free single-file call map.

The whole-project call graph (:meth:`codexray.call_graph.CallGraph.build`) is the
accurate cross-file resolver, but it must parse every source file in the project
— seconds on a large repo. For the zero-config ``codexray FILE`` default we want
the *shape* of a single file's own call structure, instantly: which functions it
defines and, for each, what it calls.

Resolution is deliberately local:

- A call to another function **defined in the same file** resolves to that
  definition's line (``resolved: true``).
- A call to an imported name, a method on some receiver, or a built-in surfaces
  as an **unresolved outbound name** (``resolved: false``). Following that edge
  to its definition in another file is exactly what needs the whole-project
  graph — one ``--call-graph`` command away.
- Calls that sit outside every function (module-level wiring such as
  ``Deno.serve(handler)``) are collected under a synthetic ``(module)`` entry so
  entry-point files are not reported as empty.

The result is a compact, TOON-friendly envelope with a small health header so a
bare ``codexray FILE`` answers both "what does this file call?" and "is it safe
to touch?" in one instant call.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .core.parser import Parser
from .function_extraction import walk_tree

#: Pseudo-function name for calls made outside any function definition.
MODULE_SCOPE = "(module)"

#: Leading object identifier (optionally dotted, e.g. ``this.svc``) of a call
#: receiver. Used to collapse a receiver to its root: the raw receiver of a
#: chained call ``router.get(...).post(...)`` is the *entire preceding chain*
#: source (newlines, comments, args) — useless and enormous in a call map. We
#: keep only the root object so ``router.get`` / ``router.post`` dedupe to one
#: ``router`` receiver, and a plain ``handlers.getSettings`` stays ``handlers``.
_RECEIVER_ROOT_RE = re.compile(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*")


def _clean_receiver(receiver: str | None) -> str | None:
    """Collapse a call receiver to its root object identifier, or ``None``.

    A plain identifier / dotted path (``handlers``, ``this.svc``) is kept as-is;
    a complex expression receiver (a method chain, an ``await`` expression, a
    parenthesised call) is reduced to its leading identifier, or dropped when it
    does not start with one.
    """
    if not receiver:
        return None
    match = _RECEIVER_ROOT_RE.match(receiver.strip())
    return match.group(0) if match else None

#: Receiver-less builtin / global names that are pure noise in a call map. Only
#: dropped when the call has NO receiver AND does not resolve to a function
#: defined in this file — so ``service.getUser()`` (receiver) and a local call
#: to a project ``len``-named function are always kept. Conservative by design:
#: hiding a real edge is worse than one extra ``print`` row.
_NOISE_BUILTINS: frozenset[str] = frozenset(
    {
        # Python builtins
        "print", "len", "range", "enumerate", "zip", "map", "filter", "sorted",
        "reversed", "sum", "min", "max", "abs", "round", "any", "all", "isinstance",
        "issubclass", "getattr", "setattr", "hasattr", "delattr", "super", "type",
        "repr", "format", "hash", "id", "iter", "next", "open", "vars", "dir",
        "int", "float", "bool", "str", "bytes", "list", "dict", "set", "tuple",
        "frozenset", "bytearray", "complex",
        # JS / TS globals & ubiquitous constructors
        "Number", "String", "Boolean", "Array", "Object", "Symbol", "BigInt",
        "parseInt", "parseFloat", "isNaN", "isFinite", "require",
    }
)


def _tightest_enclosing(funcs: list[dict[str, Any]], line: int) -> dict[str, Any] | None:
    """Return the smallest-span function whose range contains ``line``.

    Mirrors :meth:`CallGraph._find_enclosing_func`: the tightest enclosing
    function wins so a call inside a nested function is attributed to the
    nested one, not its parent. ``None`` means the call is module-level.
    """
    best: dict[str, Any] | None = None
    for func in funcs:
        if func["line"] <= line <= func["end_line"]:
            if best is None or (
                (func["end_line"] - func["line"]) < (best["end_line"] - best["line"])
            ):
                best = func
    return best


def _dedupe_callees(callees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse repeat calls to the same target, keeping first line + a count.

    Two calls to ``foo()`` in one function are one edge with ``count: 2`` rather
    than two rows — the token-efficient shape an agent wants.
    """
    order: list[tuple[str | None, str]] = []
    merged: dict[tuple[str | None, str], dict[str, Any]] = {}
    for callee in callees:
        key = (callee.get("receiver"), callee["name"])
        if key not in merged:
            merged[key] = {**callee, "count": 1}
            order.append(key)
        else:
            merged[key]["count"] += 1
    return [merged[key] for key in order]


def extract_call_map(
    abs_path: str,
    language: str,
) -> dict[str, Any] | None:
    """Parse one file and return its local call map body, or ``None`` on parse failure.

    The body is ``{"function_count", "edge_count", "functions": [...]}``. Each
    function carries its ``callees`` (deduped, line-ordered). Callees defined in
    this file are ``resolved`` with a ``to`` line; the rest are outbound names.
    """
    parser = Parser()
    result = parser.parse_file(abs_path, language)
    if not result.success or result.tree is None:
        return None

    definitions, calls = walk_tree(result.tree.root_node, result.source_code, language)

    funcs: list[dict[str, Any]] = []
    for defn in definitions:
        funcs.append(
            {
                "name": defn["name"],
                "line": defn["start_line"],
                "end_line": defn.get("end_line", defn["start_line"]),
                "receiver": defn.get("class"),
            }
        )

    # A name defined in this file → a resolvable in-file target (with its line).
    defined_line: dict[str, int] = {}
    for func in funcs:
        # First definition wins when a name is defined twice; the line is only a
        # navigation hint, so an approximate one for overloads is acceptable.
        defined_line.setdefault(func["name"], func["line"])

    # Bucket each call under its enclosing function (or the module pseudo-scope).
    by_owner: dict[tuple[str, int], list[dict[str, Any]]] = {}
    module_calls: list[dict[str, Any]] = []
    for call in calls:
        name = call.get("name")
        if not name:
            continue
        receiver = _clean_receiver(call.get("receiver"))
        resolved_in_file = name in defined_line
        # Drop receiver-less builtin noise, but never an in-file-resolved call.
        if receiver is None and not resolved_in_file and name in _NOISE_BUILTINS:
            continue
        entry: dict[str, Any] = {"name": name}
        if receiver:
            entry["receiver"] = receiver
        if resolved_in_file:
            entry["resolved"] = True
            entry["to"] = defined_line[name]
        else:
            entry["resolved"] = False

        owner = _tightest_enclosing(funcs, call["line"])
        if owner is None:
            module_calls.append(entry)
        else:
            by_owner.setdefault((owner["name"], owner["line"]), []).append(entry)

    out_functions: list[dict[str, Any]] = []
    edge_count = 0
    for func in funcs:
        callees = _dedupe_callees(by_owner.get((func["name"], func["line"]), []))
        edge_count += sum(c["count"] for c in callees)
        row: dict[str, Any] = {
            "name": func["name"],
            "line": func["line"],
            "end_line": func["end_line"],
            "callee_count": len(callees),
            "callees": callees,
        }
        if func["receiver"]:
            row["receiver"] = func["receiver"]
        out_functions.append(row)

    if module_calls:
        module_callees = _dedupe_callees(module_calls)
        edge_count += sum(c["count"] for c in module_callees)
        out_functions.insert(
            0,
            {
                "name": MODULE_SCOPE,
                "line": 0,
                "end_line": 0,
                "callee_count": len(module_callees),
                "callees": module_callees,
            },
        )

    return {
        "function_count": len(funcs),
        "edge_count": edge_count,
        "functions": out_functions,
    }


def _summary_line(rel_path: str, grade: str, risk: str, body: dict[str, Any]) -> str:
    return (
        f"{rel_path} grade={grade} risk={risk} "
        f"functions={body['function_count']} calls={body['edge_count']}"
    )


def build_call_map_result(
    abs_path: str,
    language: str,
    *,
    rel_path: str | None = None,
    project_root: str | None = None,
) -> dict[str, Any]:
    """Assemble the full ``call_map`` envelope: health header + call-map body.

    The header (grade, score, risk) reuses the same single-file scorer as
    ``--smart-context`` so the two agree, but skips the whole-project dependency
    lookup — risk is computed index-free (downstream count omitted), keeping the
    default instant. When the file cannot be parsed, a degraded envelope with an
    empty call map is returned (``parse_ok: false``) rather than an error, so a
    consumer can still read the header.
    """
    from .health_scorer import HealthScorer
    from .mcp.tools.smart_context_tool import _quick_risk, _risk_to_verdict
    from .mcp.tools.utils.test_discovery import find_test_files

    display_path = rel_path or Path(abs_path).name
    root = project_root or str(Path(abs_path).resolve().parent)

    try:
        line_count = len(
            Path(abs_path).read_text(encoding="utf-8", errors="replace").splitlines()
        )
    except OSError:
        line_count = 0

    health = HealthScorer().score_file(abs_path)
    grade = health.grade
    score = round(health.total, 1)
    has_tests = bool(find_test_files(abs_path, root))
    # downstream=0: a local map never builds the project graph, so dependents are
    # not counted here. --smart-context is the command that factors them in.
    risk = _quick_risk(0, grade, has_tests)

    body = extract_call_map(abs_path, language)
    parse_ok = body is not None
    if body is None:
        body = {"function_count": 0, "edge_count": 0, "functions": []}

    summary_line = _summary_line(display_path, grade, risk, body)
    return {
        "success": True,
        "mode": "call_map",
        "file": display_path,
        "language": language,
        "line_count": line_count,
        "parse_ok": parse_ok,
        "health": {"grade": grade, "score": score},
        "risk": risk,
        "verdict": _risk_to_verdict(risk),
        "function_count": body["function_count"],
        "edge_count": body["edge_count"],
        "functions": body["functions"],
        "summary_line": summary_line,
        "agent_summary": {
            "summary_line": summary_line,
            "verdict": _risk_to_verdict(risk),
            "grade": grade,
            "risk": risk,
            "function_count": body["function_count"],
            "edge_count": body["edge_count"],
            "next_step": (
                "Read the callees to see what this file drives. To follow an "
                "outbound call into its definition across files, run "
                "`codexray --project-root . --call-graph chain "
                "--call-graph-function <name> --format json`."
            ),
        },
    }
