#!/usr/bin/env python3
"""Unit tests for the zero-argument agent default dispatcher.

``_apply_agent_defaults`` turns a bare ``codexray [PATH]`` invocation into the
single most useful command: a file → ``--smart-context``, a directory / ``.`` /
no path → ``--overview``, defaulting output to ``--format toon``. Any explicit
action flag must pass through untouched (non-breaking).
"""

import pytest

from codexray.cli_main import _apply_agent_defaults


@pytest.fixture
def sample_file(tmp_path):
    path = tmp_path / "module.py"
    path.write_text("def f():\n    return 1\n", encoding="utf-8")
    return path


class TestFileTarget:
    """A file target routes to --smart-context."""

    def test_bare_file_gets_smart_context_and_toon(self, sample_file):
        argv = _apply_agent_defaults([str(sample_file)])
        assert argv == [str(sample_file), "--smart-context", "--format", "toon"]

    def test_explicit_format_is_preserved(self, sample_file):
        argv = _apply_agent_defaults([str(sample_file), "--format", "json"])
        assert argv == [str(sample_file), "--smart-context", "--format", "json"]
        assert argv.count("--format") == 1

    def test_output_format_counts_as_format_choice(self, sample_file):
        argv = _apply_agent_defaults([str(sample_file), "--output-format", "text"])
        assert "--format" not in argv
        assert argv == [
            str(sample_file),
            "--smart-context",
            "--output-format",
            "text",
        ]


class TestDirectoryTarget:
    """A directory / '.' / missing path routes to --overview."""

    def test_dot_gets_overview_rooted_at_dot(self):
        argv = _apply_agent_defaults(["."])
        assert argv == ["--overview", "--project-root", ".", "--format", "toon"]

    def test_directory_is_rooted_via_project_root(self, tmp_path):
        argv = _apply_agent_defaults([str(tmp_path)])
        assert argv == [
            "--overview",
            "--project-root",
            str(tmp_path),
            "--format",
            "toon",
        ]

    def test_no_path_gives_overview_of_cwd(self):
        argv = _apply_agent_defaults([])
        assert argv == ["--overview", "--format", "toon"]

    def test_explicit_project_root_is_not_duplicated(self, tmp_path):
        argv = _apply_agent_defaults([".", "--project-root", str(tmp_path)])
        assert argv.count("--project-root") == 1
        assert argv == [
            "--overview",
            "--project-root",
            str(tmp_path),
            "--format",
            "toon",
        ]


class TestExplicitActionsPassThrough:
    """Any real action flag leaves argv exactly as-is."""

    @pytest.mark.parametrize(
        "argv",
        [
            ["file.py", "--advanced"],
            ["--overview"],
            ["--table", "full", "file.py"],
            ["--smart-context", "file.py"],
            ["--help"],
            ["--version"],
            ["file.py", "--call-graph", "callers", "--call-graph-function", "f"],
        ],
    )
    def test_action_flags_untouched(self, argv):
        assert _apply_agent_defaults(list(argv)) == argv


class TestModifierEdgeCases:
    """Pass-through modifiers and unusual shapes."""

    def test_equals_form_format_is_respected(self, sample_file):
        argv = _apply_agent_defaults([str(sample_file), "--format=json"])
        assert argv == [str(sample_file), "--smart-context", "--format=json"]

    def test_quiet_modifier_is_kept(self, sample_file):
        argv = _apply_agent_defaults([str(sample_file), "--quiet"])
        assert argv == [str(sample_file), "--smart-context", "--quiet", "--format", "toon"]

    def test_two_positionals_bail_out(self, sample_file):
        raw = [str(sample_file), "other.py"]
        assert _apply_agent_defaults(list(raw)) == raw

    def test_nonexistent_path_falls_back_to_overview(self, tmp_path):
        missing = str(tmp_path / "nope")
        argv = _apply_agent_defaults([missing])
        assert argv[0] == "--overview"
        assert "--project-root" in argv
        assert missing in argv
