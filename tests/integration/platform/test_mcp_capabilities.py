from unittest.mock import patch

import pytest

from codexray.mcp.server import CodeXrayMCPServer
from codexray.platform_compat.detector import PlatformInfo


class TestMCPCapabilities:
    @pytest.mark.skip(
        reason="Tool imports moved into lazy _create_tool_registry in "
        "v1.13.0; the patch targets (QueryTool/ReadPartialTool/etc as "
        "mcp.server module attributes) no longer exist. Re-baseline the "
        "patching strategy."
    )
    def test_platform_info_in_metadata(self):
        """
        Property 14: MCP capability consistency
        Validates: Requirements 7.5
        """
        with patch("codexray.mcp.server.PlatformDetector") as mock_detector:
            mock_detector.detect.return_value = PlatformInfo(
                os_name="test_os",
                os_version="1.0",
                python_version="3.10",
                platform_key="test_os-3.10",
            )

            # Mock other dependencies to avoid side effects
            with (
                patch("codexray.mcp.server.get_analysis_engine"),
                patch("codexray.mcp.server.SecurityValidator"),
                patch("codexray.mcp.server.QueryTool"),
                patch("codexray.mcp.server.ReadPartialTool"),
                patch("codexray.mcp.server.AnalyzeCodeStructureTool"),
                patch("codexray.mcp.server.AnalyzeScaleTool"),
                patch("codexray.mcp.server.ListFilesTool"),
                patch("codexray.mcp.server.SearchContentTool"),
                patch("codexray.mcp.server.FindAndGrepTool"),
            ):
                server = CodeXrayMCPServer()

                assert "test_os-3.10" in server.version
