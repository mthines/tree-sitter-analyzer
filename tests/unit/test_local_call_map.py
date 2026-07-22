#!/usr/bin/env python3
"""Unit tests for the fast, index-free single-file call map."""

from __future__ import annotations

from pathlib import Path

import pytest

from codexray.local_call_map import (
    MODULE_SCOPE,
    build_call_map_result,
    extract_call_map,
)

PY_SOURCE = '''\
import os


def helper(x):
    return x + 1


def caller():
    helper(1)
    helper(2)
    os.getcwd()
    return len([1, 2, 3])


class Service:
    def run(self):
        caller()
        self.helper_method()


helper(99)
'''


@pytest.fixture
def py_file(tmp_path: Path) -> Path:
    path = tmp_path / "sample.py"
    path.write_text(PY_SOURCE, encoding="utf-8")
    return path


def _func(result: dict, name: str) -> dict:
    return next(f for f in result["functions"] if f["name"] == name)


def _callee_names(func: dict) -> list[str]:
    return [c["name"] for c in func["callees"]]


class TestExtractCallMap:
    def test_in_file_calls_resolve_to_a_line(self, py_file: Path):
        result = extract_call_map(str(py_file), "python")
        caller = _func(result, "caller")
        helper_edge = next(c for c in caller["callees"] if c["name"] == "helper")
        assert helper_edge["resolved"] is True
        assert helper_edge["to"] == 4  # def helper is on line 4
        assert helper_edge["count"] == 2  # called twice → deduped with count

    def test_outbound_calls_are_unresolved(self, py_file: Path):
        result = extract_call_map(str(py_file), "python")
        caller = _func(result, "caller")
        os_edge = next(c for c in caller["callees"] if c["name"] == "getcwd")
        assert os_edge["resolved"] is False
        assert os_edge["receiver"] == "os"

    def test_receiverless_builtins_are_filtered(self, py_file: Path):
        result = extract_call_map(str(py_file), "python")
        caller = _func(result, "caller")
        # len(...) is a receiver-less builtin → dropped as noise.
        assert "len" not in _callee_names(caller)

    def test_receiver_methods_are_kept(self, py_file: Path):
        result = extract_call_map(str(py_file), "python")
        run = _func(result, "run")
        names = _callee_names(run)
        assert "caller" in names  # resolves in-file
        assert "helper_method" in names  # receiver method, kept even if unresolved

    def test_module_level_calls_bucketed(self, py_file: Path):
        result = extract_call_map(str(py_file), "python")
        module = _func(result, MODULE_SCOPE)
        helper_edge = next(c for c in module["callees"] if c["name"] == "helper")
        assert helper_edge["resolved"] is True

    def test_edge_count_matches_sum(self, py_file: Path):
        result = extract_call_map(str(py_file), "python")
        total = sum(sum(c["count"] for c in f["callees"]) for f in result["functions"])
        assert result["edge_count"] == total

    def test_parse_failure_returns_none(self, tmp_path: Path):
        bad = tmp_path / "broken.py"
        bad.write_text("def (:::\n", encoding="utf-8")
        # tree-sitter is error-tolerant, so a broken file still parses to a tree;
        # a truly unreadable path is the real None path.
        assert extract_call_map(str(tmp_path / "does_not_exist.py"), "python") is None


class TestBuildCallMapResult:
    def test_header_and_envelope(self, py_file: Path):
        result = build_call_map_result(
            str(py_file), "python", rel_path="sample.py", project_root=str(py_file.parent)
        )
        assert result["success"] is True
        assert result["mode"] == "call_map"
        assert result["file"] == "sample.py"
        assert result["language"] == "python"
        assert result["parse_ok"] is True
        assert result["health"]["grade"] in {"A", "B", "C", "D", "F"}
        assert result["risk"] in {"safe", "caution", "dangerous"}
        assert result["verdict"] in {"SAFE", "CAUTION", "UNSAFE"}
        assert "functions" in result
        assert result["summary_line"].startswith("sample.py grade=")
        assert result["agent_summary"]["function_count"] == result["function_count"]

    def test_unreadable_file_degrades(self, tmp_path: Path):
        result = build_call_map_result(
            str(tmp_path / "missing.py"),
            "python",
            rel_path="missing.py",
            project_root=str(tmp_path),
        )
        assert result["success"] is True
        assert result["parse_ok"] is False
        assert result["functions"] == []
