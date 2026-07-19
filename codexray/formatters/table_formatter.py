#!/usr/bin/env python3
"""
Table Formatter — canonical public location.

Re-exports LegacyTableFormatter as TableFormatter.
The implementation lives in codexray/legacy_table_formatter.py;
this module provides the Phase-7 canonical import path.
"""

from ..legacy_table_formatter import LegacyTableFormatter as TableFormatter

__all__ = ["TableFormatter"]
