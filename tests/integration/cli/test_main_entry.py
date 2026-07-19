#!/usr/bin/env python3
"""
Tests for codexray.__main__ module

Provides tests for the main entry point.
"""

import pytest


class TestMainEntry:
    """Test class for __main__.py"""

    def test_cli_integration_availability(self):
        """Test CLI integration availability"""
        try:
            from codexray import cli

            assert hasattr(cli, "main")
        except ImportError:
            pytest.fail("CLI module not available")
