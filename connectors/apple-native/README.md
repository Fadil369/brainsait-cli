# BrainSAIT Apple Bridge

A native MCP connector that bridges **Apple Shortcuts** and **Automator** to Claude.
It runs on your Mac (that's where Shortcuts and Automator live) and can be used two ways:

| Mode | Transport | Claude surface |
|------|-----------|----------------|
| Local | stdio | Claude Desktop, Claude Code |
| Remote | Streamable HTTP (`/mcp`) | claude.ai **Custom Connectors** (via a tunnel) |

## Tools exposed to Claude

| Tool | What it does |
|------|--------------|
| `get_bridge_status` | Check macOS availability, CLI paths, and security config |
| `list_shortcuts` | List Shortcuts (with identifiers), optionally by folder |
| `run_shortcut` | Run a shortcut with optional text input, capture its output |
| `open_shortcut_in_editor` | Open a shortcut in the Shortcuts editor |
| `list_automator_workflows` | Find `.workflow` bundles in allowed directories |
| `describe_automator_workflow` | Summarize a workflow's type and action chain |
| `run_automator_workflow` | Run a workflow with optional input and variable overrides |
| `run_applescript` | Raw AppleScript (opt-in via `APPLE_BRIDGE_ALLOW_APPLESCRIPT=1`) |
| `run_bridge_pipeline` | **The bridge**: chain Shortcuts ↔ Automator ↔ AppleScript steps, piping each step's output into the next |

Example pipeline Claude can run with one tool call:

```json
{
  "steps": [
    { "kind": "shortcut", "target": "Fetch Inbox Summary" },
    { "kind": "automator", "target": "~/Library/Services/Save Report.workflow" }
  ],
  "initial_input": "today"
}
```

## Install (on your Mac)

Requires macOS 12+ (the `shortcuts` CLI) and Python 3.10+.

```bash
cd connectors/apple-native
uv venv && source .venv/bin/activate
uv pip install -e .
```

Grant automation permissions on first run: System Settings → Privacy & Security →
Automation, allow your terminal (or the launchd agent) to control Shortcuts Events /
target apps.

## Mode 1 — Claude Desktop / Claude Code (stdio)

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-bridge": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/brainsait-cli/connectors/apple-native",
        "run", "brainsait-apple-bridge", "--transport", "stdio"
      ],
      "env": {
        "APPLE_BRIDGE_ALLOWED_SHORTCUTS": "",
        "APPLE_BRIDGE_ALLOW_APPLESCRIPT": "0"
      }
    }
  }
}
```

For Claude Code: `claude mcp add apple-bridge -- uv --directory /path/to/connectors/apple-native run brainsait-apple-bridge`

Or via the BrainSAIT CLI: `brainsait connector apple --transport stdio`

## Mode 2 — claude.ai Custom Connector (HTTP + tunnel)

1. Start the HTTP server on the Mac:

   ```bash
   export APPLE_BRIDGE_TOKEN="$(openssl rand -hex 24)"   # keep this secret
   brainsait-apple-bridge --transport http --port 8848
   ```

2. Expose it with a tunnel (Cloudflare shown; Tailscale Funnel/ngrok work too):

   ```bash
   cloudflared tunnel --url http://127.0.0.1:8848
   ```

3. In claude.ai → **Settings → Connectors → Add custom connector**, set the URL to:

   ```
   https://<your-tunnel-host>/mcp?token=<APPLE_BRIDGE_TOKEN>
   ```

   The token is checked on every request (`Authorization: Bearer …` also works).
   For production, prefer a named Cloudflare tunnel + Cloudflare Access instead of
   a quick tunnel, and keep the token set as defense in depth.

To keep it running at login, install the launchd agent:

```bash
./scripts/install.sh          # renders + loads com.brainsait.apple-bridge.plist
```

## Security model

- **Shortcut allowlist** — `APPLE_BRIDGE_ALLOWED_SHORTCUTS="Name One,Name Two"` restricts
  which shortcuts can run (empty = all).
- **Workflow directory containment** — Automator workflows only run from
  `~/Library/Services`, `~/Library/Workflows`, `~/Documents/Automator`, plus
  `APPLE_BRIDGE_WORKFLOW_DIRS` (comma-separated). Paths are resolved and checked.
- **AppleScript gate** — raw AppleScript is off unless `APPLE_BRIDGE_ALLOW_APPLESCRIPT=1`.
- **Token auth** on the HTTP transport (`APPLE_BRIDGE_TOKEN`), constant-time compared.
- **Timeouts** — every run is bounded (`APPLE_BRIDGE_TIMEOUT`, default 120s, capped at 600s).

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `APPLE_BRIDGE_TOKEN` | *(empty)* | Shared secret for the HTTP transport |
| `APPLE_BRIDGE_ALLOWED_SHORTCUTS` | *(all)* | Comma-separated shortcut allowlist |
| `APPLE_BRIDGE_WORKFLOW_DIRS` | *(built-ins)* | Extra Automator workflow directories |
| `APPLE_BRIDGE_ALLOW_APPLESCRIPT` | `0` | Enable the `run_applescript` tool |
| `APPLE_BRIDGE_TIMEOUT` | `120` | Default per-run timeout in seconds |
| `APPLE_BRIDGE_HOST` / `APPLE_BRIDGE_PORT` | `127.0.0.1` / `8848` | HTTP bind address |

## Development

```bash
uv pip install -e ".[dev]"
pytest tests/ -q                       # runs anywhere; macOS CLIs are mocked
npx @modelcontextprotocol/inspector uv run brainsait-apple-bridge   # interactive testing
```
