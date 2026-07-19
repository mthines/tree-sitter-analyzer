"""Argument parser construction for the codexray CLI.

This module is the assembler: it imports all ``_add_*`` helpers from the
``argument_groups`` sub-package and wires them together into a single
``argparse.ArgumentParser``.  Each helper lives in a focused module:

    argument_groups/_core.py       — core, output, project/logging, partial-read, batch
    argument_groups/_query.py      — query selection, SQL platform
    argument_groups/_analysis.py   — analysis, health, change-impact, dependency/graph flags
    argument_groups/_mcp.py        — index management, constraints, clean-state
    argument_groups/_agents.py     — agent skills, agent workflow
    argument_groups/_advanced.py   — trace-impact, env probe, modification guard,
                                     decision journal, batch search
"""

from __future__ import annotations

import argparse

from .argument_groups import (
    _add_agent_skills_options,
    _add_agent_workflow_options,
    _add_analysis_options,
    _add_batch_options,
    _add_batch_search_options,
    _add_clean_state_options,
    _add_core_options,
    _add_decision_journal_options,
    _add_environment_probe_options,
    _add_install_skills_options,
    _add_mcp_analysis_options,
    _add_mcp_change_options,
    _add_mcp_constraints_options,
    _add_mcp_health_options,
    _add_mcp_index_management_options,
    _add_modification_guard_options,
    _add_output_options,
    _add_partial_read_options,
    _add_project_and_logging_options,
    _add_query_options,
    _add_sql_platform_options,
    _add_trace_impact_options,
)

# Re-export so that existing imports from this module continue to work.
__all__ = [
    "CLI_EPILOG",
    "create_argument_parser",
    "_add_agent_skills_options",
    "_add_agent_workflow_options",
    "_add_analysis_options",
    "_add_batch_options",
    "_add_batch_search_options",
    "_add_clean_state_options",
    "_add_core_options",
    "_add_decision_journal_options",
    "_add_environment_probe_options",
    "_add_install_skills_options",
    "_add_mcp_analysis_options",
    "_add_mcp_change_options",
    "_add_mcp_constraints_options",
    "_add_mcp_equivalent_options",
    "_add_mcp_health_options",
    "_add_mcp_index_management_options",
    "_add_modification_guard_options",
    "_add_output_options",
    "_add_partial_read_options",
    "_add_project_and_logging_options",
    "_add_query_options",
    "_add_sql_platform_options",
    "_add_trace_impact_options",
]

CLI_EPILOG = (
    "Examples:  (grouped by task)\n"
    "\n"
    "Cold-start  (1 call, full file picture — use these first):\n"
    "  codexray file.py --smart-context         Killer 1-call: health, exports, structure, deps, edit risk\n"
    "  codexray --overview                      Project portrait + health summary\n"
    "  codexray agent-skills                    Project-local agent skill inventory\n"
    "  codexray agent-workflow file.py          SMART workflow command pack\n"
    "\n"
    "Read code  (extract content from a single file):\n"
    "  codexray file.java --table=full          Markdown table of classes/methods\n"
    "  codexray file.java --structure           Structure overview in JSON\n"
    "  codexray file.java --summary             Quick summary of classes/methods\n"
    "  codexray file.java --advanced            Full analysis with all elements\n"
    "  codexray file.java --query-key class     Extract all class definitions\n"
    "  codexray file.java --partial-read --start-line 10 --end-line 20\n"
    "\n"
    "Health  (per-file or project-wide grading):\n"
    "  codexray file.py --file-health           A-F health grade + signal + smells\n"
    "  codexray file-health file.py             Agent-friendly alias for --file-health\n"
    "  codexray --project-health                Score ALL project files\n"
    "  codexray --watch-health                  Daemon: alert when health grades drop\n"
    "\n"
    "Edit safety  (risk + impact before/after a change):\n"
    "  codexray file.py --safe-to-edit --edit-type refactor\n"
    "  codexray file.py --refactor              Refactoring suggestions with plans\n"
    "  codexray --change-impact                 Git diff impact (trimmed surface by default)\n"
    "  codexray --change-impact --change-impact-resource-profile local_low_impact\n"
    "  codexray --change-impact --change-impact-full   Full verbose envelope (~145 KB)\n"
    "  codexray change-impact --change-impact-mode staged\n"
    "\n"
    "Graph & deps  (cross-file relationships):\n"
    "  codexray --dependencies summary          Project dependency summary\n"
    "  codexray file.py --dependencies file_deps  File dependency graph\n"
    "  codexray --detect-routes                 URL→handler routes (Flask/Django/FastAPI/Express/Spring)\n"
    "  codexray detect-routes --detect-routes-mode all\n"
    "  codexray --codegraph-overview            Entry points, dead code, hubs, coupling\n"
    "  codexray --codegraph-navigate SYMBOL     Go-to-def + refs + call hierarchy\n"
    "\n"
    "Architecture rules  (constraint DSL):\n"
    "  codexray --check-constraints             Evaluate architectural-constraints.yml\n"
    "  codexray --check-constraints --severity-min error\n"
    "\n"
    "Cache ops  (manage the pre-indexed AST cache):\n"
    "  codexray --autoindex                     Idempotent cache status / warm\n"
    "  codexray --autoindex --autoindex-mode warm\n"
    "  codexray --full-index                    Force a fresh full re-index\n"
    "  codexray --codegraph-metrics             Cross-domain project dashboard\n"
    "  codexray --clean-state                   Remove ephemeral workspace state\n"
    "  codexray --clean-state-dry-run           Preview what --clean-state would remove\n"
    "\n"
    "Discovery  (what does this CLI know?):\n"
    "  codexray parser-readiness swift          Parser/plugin readiness advisor\n"
    "  codexray --list-queries                  Show available query keys\n"
    "  codexray --show-supported-languages      List supported languages\n"
)


def _add_mcp_equivalent_options(parser: argparse.ArgumentParser) -> None:
    """Add CLI flags that mirror MCP tools."""
    _add_agent_skills_options(parser)
    _add_agent_workflow_options(parser)
    _add_mcp_health_options(parser)
    _add_mcp_change_options(parser)
    _add_mcp_analysis_options(parser)
    _add_mcp_constraints_options(parser)
    # consolidated-only families (ported during merge of feat/autonomous-dev)
    _add_trace_impact_options(parser)
    _add_environment_probe_options(parser)
    _add_modification_guard_options(parser)
    _add_decision_journal_options(parser)
    _add_batch_search_options(parser)
    # PL-C sprint additions
    _add_mcp_index_management_options(parser)
    _add_clean_state_options(parser)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze code using Tree-sitter and extract structured information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=CLI_EPILOG,
    )
    _add_core_options(parser)
    _add_query_options(parser)
    _add_output_options(parser)
    _add_analysis_options(parser)
    _add_sql_platform_options(parser)
    _add_project_and_logging_options(parser)
    _add_partial_read_options(parser)
    _add_batch_options(parser)
    _add_install_skills_options(parser)
    _add_mcp_equivalent_options(parser)
    return parser
