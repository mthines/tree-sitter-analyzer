# MCP client setup

> Per-client MCP setup, moved out of the README to keep it lean. Back to the [README](../README.md).

<details>
<summary><b>📘 Claude Code</b> (recommended)</summary>

```bash
claude mcp add codexray \
  --env TREE_SITTER_PROJECT_ROOT="$PWD" \
  -- uvx --from "codexray[mcp]" codexray-mcp
```

Verify: `claude mcp list`. The 13 `tsa-*` skills auto-discover from `.claude/skills/`.

**PyPI / uvx users** — install the bundled skills once with:
```bash
codexray --install-skills              # into ./.claude/skills/ (this project)
codexray --install-skills-global       # into ~/.claude/skills/ (all projects)
```
Git-clone users already have them — no action needed.
</details>

<details>
<summary><b>📗 Claude Desktop</b></summary>

Edit `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`, Linux: `~/.config/Claude/`):

```json
{
  "mcpServers": {
    "codexray": {
      "command": "uvx",
      "args": ["--from", "codexray[mcp]", "codexray-mcp"],
      "env": { "TREE_SITTER_PROJECT_ROOT": "/absolute/path/to/your/project" }
    }
  }
}
```
</details>

<details>
<summary><b>📙 GitHub Copilot (VS Code)</b></summary>

Create `.vscode/mcp.json` (note: `servers`, not `mcpServers`):

```json
{
  "servers": {
    "codexray": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "codexray[mcp]", "codexray-mcp"],
      "env": { "TREE_SITTER_PROJECT_ROOT": "${workspaceFolder}" }
    }
  }
}
```
</details>

<details>
<summary><b>🖱 Cursor / Cline / Continue / Roo Code</b></summary>

All read the same `mcpServers` schema as Claude Desktop. Cursor: **Settings → MCP**. Cline: MCP panel → Edit settings. Continue: `~/.continue/config.json` under `experimental.modelContextProtocolServers`. Roo Code: MCP panel → Edit MCP Settings.
</details>

<details>
<summary><b>🐳 Docker</b> (no local Python / uv)</summary>

The repo ships a [`Dockerfile`](Dockerfile) that builds the MCP server (stdio transport) from source, so the image always matches the committed code.

```bash
# Build once
docker build -t codexray-mcp .

# Run against the current repo (server speaks MCP over stdio; -i keeps stdin open)
docker run --rm -i --user "$(id -u):$(id -g)" \
  -v "$PWD:/work" -w /work codexray-mcp
```

`--user "$(id -u):$(id -g)"` runs as your host UID/GID, so the `.ast-cache/`, decision journal, and any `edit` writes under the bind-mounted repo are owned by you, not root.

MCP client config (the project root inside the container is the mount point `/work`):

```json
{
  "mcpServers": {
    "codexray": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--user", "1000:1000",
        "-v", "/absolute/path/to/your/project:/work",
        "-w", "/work",
        "-e", "TREE_SITTER_PROJECT_ROOT=/work",
        "codexray-mcp"
      ]
    }
  }
}
```
</details>

> ⚠️ `TREE_SITTER_PROJECT_ROOT` must be **absolute**. The server enforces a security boundary against escapes via `SecurityValidator`.
