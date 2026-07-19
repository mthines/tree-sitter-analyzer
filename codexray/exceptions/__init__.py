#!/usr/bin/env python3
"""
CodeXray Custom Exceptions

Public facade for the exception hierarchy and handling utilities. Keep imports from
``codexray.exceptions`` stable while the implementation lives in
smaller private modules.
"""

from .core import (
    AnalysisError,
    CodeXrayError,
    ConfigurationError,
    FileHandlingError,
    LanguageNotSupportedError,
    MCPError,
    ParseError,
    PluginError,
    QueryError,
    ValidationError,
)
from .execution import (
    create_error_response,
    handle_exception,
    handle_exceptions,
    safe_execute,
    safe_execute_async,
)
from .mcp import (
    MCPResourceError,
    MCPTimeoutError,
    MCPToolError,
    MCPValidationError,
    _sanitize_error_context,
    create_mcp_error_response,
    mcp_exception_handler,
)
from .security import (
    FileRestrictionError,
    PathTraversalError,
    RegexSecurityError,
    SecurityError,
)

__all__ = [
    "AnalysisError",
    "ConfigurationError",
    "FileHandlingError",
    "FileRestrictionError",
    "LanguageNotSupportedError",
    "MCPError",
    "MCPResourceError",
    "MCPTimeoutError",
    "MCPToolError",
    "MCPValidationError",
    "ParseError",
    "PathTraversalError",
    "PluginError",
    "QueryError",
    "RegexSecurityError",
    "SecurityError",
    "CodeXrayError",
    "ValidationError",
    "_sanitize_error_context",
    "create_error_response",
    "create_mcp_error_response",
    "handle_exception",
    "handle_exceptions",
    "mcp_exception_handler",
    "safe_execute",
    "safe_execute_async",
]

for _name in __all__:
    _obj = globals()[_name]
    if hasattr(_obj, "__module__"):
        _obj.__module__ = __name__

del _name, _obj
