#!/usr/bin/env python3
"""
CodeXray — Tree-sitter Multi-Language Code Analyzer

A comprehensive Python library for analyzing code across multiple programming languages
using Tree-sitter. Features a plugin-based architecture for extensible language support.

Upstream / credits:
    CodeXray is a fork of the ``tree-sitter-analyzer`` project by aisheng.yu
    (https://github.com/aimasteracc/tree-sitter-analyzer, MIT). It repackages that
    work under a shorter, more memorable name with a CLI-first (JSON + ``jq``)
    workflow for easier day-to-day use, and adds stronger TypeScript/JavaScript
    call-graph resolution plus a global extraction cache. All upstream authorship
    is retained (see ``__author__`` below and the ``Upstream`` link in pyproject).

Architecture:
- Core Engine: UniversalCodeAnalyzer, LanguageDetector, QueryLoader
- Plugin System: Extensible language-specific analyzers and extractors
- Data Models: Generic and language-specific code element representations
"""

__version__ = "1.29.0"
__author__ = "aisheng.yu"
__email__ = "aimasteracc@gmail.com"

import importlib as _importlib
from typing import Any as _Any

# Legacy public names remain import-compatible, but loading them eagerly makes
# the MCP stdio server pay for analysis_engine/models/output_manager before the
# client even receives initialize. PEP 562 keeps import codexray
# cheap while preserving from codexray import Function.
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "UniversalCodeAnalyzer": (
        "codexray.core.analysis_engine",
        "UnifiedAnalysisEngine",
    ),
    "EncodingManager": ("codexray.encoding_utils", "EncodingManager"),
    "detect_encoding": ("codexray.encoding_utils", "detect_encoding"),
    "extract_text_slice": ("codexray.encoding_utils", "extract_text_slice"),
    "read_file_safe": ("codexray.encoding_utils", "read_file_safe"),
    "safe_decode": ("codexray.encoding_utils", "safe_decode"),
    "safe_encode": ("codexray.encoding_utils", "safe_encode"),
    "write_file_safe": ("codexray.encoding_utils", "write_file_safe"),
    "LanguageDetector": ("codexray.language_detector", "LanguageDetector"),
    "get_loader": ("codexray.language_loader", "get_loader"),
    "AnalysisResult": ("codexray.models", "AnalysisResult"),
    "Class": ("codexray.models", "Class"),
    "CodeElement": ("codexray.models", "CodeElement"),
    "Function": ("codexray.models", "Function"),
    "Import": ("codexray.models", "Import"),
    "JavaAnnotation": ("codexray.models", "JavaAnnotation"),
    "JavaClass": ("codexray.models", "JavaClass"),
    "JavaField": ("codexray.models", "JavaField"),
    "JavaImport": ("codexray.models", "JavaImport"),
    "JavaMethod": ("codexray.models", "JavaMethod"),
    "JavaPackage": ("codexray.models", "JavaPackage"),
    "Variable": ("codexray.models", "Variable"),
    "OutputManager": ("codexray.output_manager", "OutputManager"),
    "get_output_manager": ("codexray.output_manager", "get_output_manager"),
    "output_data": ("codexray.output_manager", "output_data"),
    "output_error": ("codexray.output_manager", "output_error"),
    "output_info": ("codexray.output_manager", "output_info"),
    "output_warning": ("codexray.output_manager", "output_warning"),
    "set_output_mode": ("codexray.output_manager", "set_output_mode"),
    "ElementExtractor": ("codexray.plugins", "ElementExtractor"),
    "LanguagePlugin": ("codexray.plugins", "LanguagePlugin"),
    "PluginManager": ("codexray.plugins.manager", "PluginManager"),
    "QueryLoader": ("codexray.query_loader", "QueryLoader"),
    "get_query_loader": ("codexray.query_loader", "get_query_loader"),
    "QuietMode": ("codexray.utils", "QuietMode"),
    "log_debug": ("codexray.utils", "log_debug"),
    "log_error": ("codexray.utils", "log_error"),
    "log_info": ("codexray.utils", "log_info"),
    "log_performance": ("codexray.utils", "log_performance"),
    "log_warning": ("codexray.utils", "log_warning"),
    "safe_print": ("codexray.utils", "safe_print"),
}


def __getattr__(name: str) -> _Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'codexray' has no attribute {name!r}")
    module_path, attr_name = _LAZY_EXPORTS[name]
    value = getattr(_importlib.import_module(module_path), attr_name)
    globals()[name] = value
    return value


__all__ = [
    # Core Models (optimized)
    "JavaAnnotation",
    "JavaClass",
    "JavaImport",
    "JavaMethod",
    "JavaField",
    "JavaPackage",
    "AnalysisResult",
    # Model classes
    "Class",
    "CodeElement",
    "Function",
    "Import",
    "Variable",
    # Plugin system
    "ElementExtractor",
    "LanguagePlugin",
    "PluginManager",
    "QueryLoader",
    # Language detection
    "LanguageDetector",
    # Core Components (optimized)
    # "AdvancedAnalyzer",  # Removed - migrated to plugin system
    "get_loader",
    "get_query_loader",
    # New Utilities
    "log_info",
    "log_warning",
    "log_error",
    "log_debug",
    "QuietMode",
    "safe_print",
    "log_performance",
    # Output Management
    "OutputManager",
    "set_output_mode",
    "get_output_manager",
    "output_info",
    "output_warning",
    "output_error",
    "output_data",
    # Legacy Components (backward compatibility)
    "UniversalCodeAnalyzer",
    # Version
    "__version__",
    # Encoding utilities
    "EncodingManager",
    "safe_encode",
    "safe_decode",
    "detect_encoding",
    "read_file_safe",
    "write_file_safe",
    "extract_text_slice",
]
