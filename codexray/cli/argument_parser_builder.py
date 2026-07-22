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
    "CLI_DESCRIPTION",
    "CLI_EPILOG",
    "CLI_USAGE",
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

# Short usage line — replaces argparse's auto-generated wall of every flag, which
# is unreadable for both humans and LLMs on a 300+ flag CLI.
CLI_USAGE = (
    "codexray [PATH]                      # zero-config: FILE -> call-map, DIR/. -> overview\n"
    "       codexray [FILE] "
    "[--call-map | --smart-context | --call-graph MODE --call-graph-function FN | "
    "--table full | --detect-routes | --project-health | ...] "
    "[--format json|toon|text] [--project-root DIR]"
)

# Front-matter shown at the very top of --help. Kept task-first and example-heavy
# so an agent can act from the first screen without reading all 300+ flags.
CLI_DESCRIPTION = (
    "Tree-sitter Analyzer (TSA) — correct, local code intelligence for AI agents "
    "and humans.\n"
    "Cross-language call graphs, symbol search, and structural queries over 20+ "
    "languages. No telemetry.\n"
    "\n"
    "ZERO-CONFIG (just point it at code — no flags needed)\n"
    "  codexray FILE     -> call-map: every function in the file + what each one calls,\n"
    "                       with a grade/risk header. Instant, no index.\n"
    "  codexray DIR | .  -> overview: project portrait + health summary (rooted at DIR).\n"
    "  codexray          -> overview of the current directory.\n"
    "  Output defaults to --format toon (compact). Add --format json to pipe through jq.\n"
    "  Any explicit flag below overrides this and runs exactly what you ask for.\n"
    "\n"
    "MOST-USED COMMANDS\n"
    "  codexray FILE\n"
    "      Call map: the file's functions and their callees (in-file calls resolved to a\n"
    "      line, imported/outbound calls shown as names). This is the bare-FILE default.\n"
    "  codexray FILE --smart-context\n"
    "      Edit-safety packet: health + exports + structure + deps + edit-risk for a file.\n"
    "  codexray --project-root . --call-graph chain "
    "--call-graph-function FN --format json\n"
    "      What FN calls, transitively. Point at the repo root, filter to one "
    "function.\n"
    "  codexray --project-root . --call-graph callers "
    "--call-graph-function FN --format json\n"
    "      Who calls FN.\n"
    "  codexray --detect-routes\n"
    "      URL -> handler routes (Flask/Django/FastAPI/Express/Spring).\n"
    "\n"
    "OUTPUT (agent-friendly)\n"
    "  --format json   Stable, jq-friendly structure — pipe to jq to keep only "
    "what you need.\n"
    "  --format toon   Compact tabular form, ~half the size of JSON.\n"
    "  --format text   Human-readable.\n"
    "  Narrow with jq, e.g. keep just the direct callees:\n"
    "    ... --call-graph chain --call-graph-function FN --format json "
    "| jq '.chain[] | select(.depth==1) | .callee.name'\n"
    "\n"
    "This is a large CLI (300+ flags). The full flag reference follows; "
    "task-grouped\n"
    "examples and jq recipes are at the very end (see 'Examples' below).\n"
)

CLI_EPILOG = (
    "Examples:  (grouped by task)\n"
    "\n"
    "Cold-start  (1 call, full picture — use these first):\n"
    "  codexray file.py                         Zero-config: same as `file.py --call-map` (toon output)\n"
    "  codexray .                               Zero-config: same as `--overview` rooted at the current dir\n"
    "  codexray file.py --call-map              File's functions + what each one calls (instant, no index)\n"
    "  codexray file.py --smart-context         Edit-safety 1-call: health, exports, structure, deps, edit risk\n"
    "  codexray --overview                      Project portrait + health summary\n"
    "  codexray agent-skills                    Project-local agent skill inventory\n"
    "  codexray agent-workflow file.py          SMART workflow command pack\n"
    "\n"
    "Call graph  (what calls what — point at the repo root, filter to one function):\n"
    "  codexray --project-root . --call-graph chain --call-graph-function FN --format json    What FN calls (transitive)\n"
    "  codexray --project-root . --call-graph callees --call-graph-function FN --format json  Direct callees of FN\n"
    "  codexray --project-root . --call-graph callers --call-graph-function FN --format json  Direct callers of FN\n"
    "  codexray --project-root . --call-graph-function FN --call-graph-file PATH --format json Disambiguate FN by file\n"
    "  codexray --project-root . --call-graph summary                                          Whole-graph node/edge counts\n"
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
    "\n"
    "Filtering with jq  (--format json is a stable, jq-friendly contract):\n"
    "\n"
    "  JSON shape by mode (the keys jq recipes rely on):\n"
    "    callees : {function, callee_count, function_indexed, callees:[{name,file,line,end_line,language}]}\n"
    "    callers : {function, caller_count, function_indexed, callers:[{name,file,line,end_line,language}]}\n"
    "    chain   : {function, depth, edge_count, chain:[{caller:{name,file,line,...}, callee:{name,file,line,...}, depth}]}\n"
    "    summary : {function_count, call_edge_count, file_count}\n"
    "\n"
    "  Recipes  (the jq filter runs in the shell, so only the slice you keep reaches the model's context):\n"
    "    # what FN calls -- direct callee names\n"
    "    ... --call-graph callees --call-graph-function FN --format json | jq -r '.callees[].name'\n"
    "    # callee name + location\n"
    "    ... --call-graph callees --call-graph-function FN --format json | jq -r '.callees[] | .name+\"  \"+.file+\":\"+(.line|tostring)'\n"
    "    # who calls FN\n"
    "    ... --call-graph callers --call-graph-function FN --format json | jq -r '.callers[].name'\n"
    "    # transitive chain, first level only\n"
    "    ... --call-graph chain --call-graph-function FN --format json | jq -r '.chain[] | select(.depth==1) | .callee.name'\n"
    "    # transitive chain, unique callees at any depth\n"
    "    ... --call-graph chain --call-graph-function FN --call-graph-depth 4 --format json | jq -r '[.chain[].callee.name] | unique[]'\n"
    "    # how many edges were found\n"
    "    ... --call-graph chain --call-graph-function FN --format json | jq '.edge_count'\n"
    "\n"
    "  Use --format json for jq; --format toon (~half the size) when feeding the whole small result to a model.\n"
    "  Empty result? function_indexed:false or a *_count of 0 means UNRESOLVED, not \"calls nothing\".\n"
    "\n"
    "Environment:\n"
    "  TREE_SITTER_PROJECT_ROOT   Absolute project root (or pass --project-root).\n"
    "  CODEXRAY_CACHE_DIR         Global extraction-cache location (default: $XDG_CACHE_HOME/codexray; legacy: TSA_CACHE_DIR).\n"
    "  CODEXRAY_DISABLE_GRAPH_CACHE  Set to 1 to disable the extraction cache (legacy: TSA_DISABLE_GRAPH_CACHE).\n"
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
        usage=CLI_USAGE,
        description=CLI_DESCRIPTION,
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
