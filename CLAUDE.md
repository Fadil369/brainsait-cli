# BrainSAIT CLI: Project Context for Claude

This file provides context for Claude when working with this codebase.

## Project Overview

**BrainSAIT CLI** is an AI-powered command-line assistant that integrates with AI providers (Anthropic Claude, OpenAI GPT) and provides native automation capabilities on macOS through Apple Shortcuts and Automator.

### Key Features
- Interactive AI chat with project context
- Code generation and review
- Deployment simulation
- **Apple Bridge MCP**: Native integration with Apple Shortcuts & Automator
- Pluggable AI backends

## Repository Structure

```
brainsait-cli/
├── cmd/brainsait/          # CLI main executable (Go)
├── connectors/
│   └── apple-native/       # Apple Bridge MCP connector (Python)
│       ├── src/            # Python package
│       ├── tests/          # Test suite
│       ├── scripts/        # Installation & launchd agent
│       └── pyproject.toml  # Python project config
├── scripts/
│   ├── install.sh          # Universal install script
│   └── mac-setup.sh        # macOS-specific automated setup
├── docs/                   # Documentation
├── MAC_SETUP.md           # Comprehensive macOS setup guide
├── CLAUDE_DESKTOP_SETUP.md # Claude Desktop/Code quick start
├── README.md              # Project overview
├── Makefile              # Common tasks
└── CLAUDE.md             # This file
```

## Tech Stack

### CLI (Go)
- **Language:** Go 1.21+
- **Framework:** Cobra (CLI)
- **Dependencies:** fsnotify, Docker
- **Build:** `go build -o brainsait-cli ./cmd/brainsait/main.go`

### Apple Bridge (Python)
- **Language:** Python 3.10+
- **MCP Framework:** stdio/HTTP transport
- **macOS APIs:** `shortcuts` CLI, AppleScript
- **Package Manager:** uv (recommended) or pip
- **Build:** See `connectors/apple-native/README.md`

## Development Workflow

### For CLI Changes
```bash
# Build and test
go build -o brainsait-cli ./cmd/brainsait/main.go
./brainsait-cli --help

# Install locally
sudo mv brainsait-cli /usr/local/bin/
```

### For Apple Bridge Changes
```bash
cd connectors/apple-native

# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Test interactively
npx @modelcontextprotocol/inspector uv run brainsait-apple-bridge

# Install locally
uv pip install -e .
brainsait-apple-bridge --transport stdio
```

### Using Makefile
```bash
make help              # Show all available commands
make build            # Build CLI
make install-mac      # Full macOS setup
make bridge-test      # Test Apple Bridge
```

## macOS Setup Instructions

### For First-Time Setup
```bash
bash scripts/mac-setup.sh        # Interactive
# or
bash scripts/mac-setup.sh --quick # No prompts
```

### For Claude Desktop Integration
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "apple-bridge": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/brainsait-cli/connectors/apple-native",
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

Then restart Claude Desktop.

### For Remote Setup (claude.ai Custom Connectors)
See `MAC_SETUP.md` section "Advanced: Remote Setup"

## Current Branch: `claude/mac-setup-4vg7yk`

**Purpose:** Complete macOS setup automation and documentation

**Changes Include:**
- ✅ `MAC_SETUP.md` - Comprehensive setup guide
- ✅ `CLAUDE_DESKTOP_SETUP.md` - Quick start for Claude Desktop/Code
- ✅ `scripts/mac-setup.sh` - Automated setup script
- ✅ `Makefile` - Common development tasks
- ✅ `CLAUDE.md` - This context file

**Deployment:** After review, merge to `main` and update README.md

## Key Design Decisions

1. **MCP for Apple Bridge** — Uses Model Context Protocol for extensibility and compatibility with Claude
2. **stdio vs HTTP transport** — stdio for Claude Desktop/Code, HTTP for claude.ai via tunnel
3. **Token-based auth** — APPLE_BRIDGE_TOKEN for HTTP mode security
4. **Allowlist security** — APPLE_BRIDGE_ALLOWED_SHORTCUTS restricts what can run
5. **Timeout bounds** — 120s default, 600s max to prevent long-running issues

## Configuration

### Environment Variables

**BrainSAIT CLI:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export BRAINSAIT_MODEL="claude-3-5-sonnet-20241022"
```

**Apple Bridge:**
```bash
export APPLE_BRIDGE_TOKEN="$(openssl rand -hex 24)"           # HTTP mode
export APPLE_BRIDGE_ALLOWED_SHORTCUTS="Shortcut One,Two"     # Allowlist
export APPLE_BRIDGE_ALLOW_APPLESCRIPT=1                       # Expert only
export APPLE_BRIDGE_TIMEOUT=300                               # Seconds
```

## Common Tasks

| Task | Command |
|------|---------|
| Build CLI | `make build` or `go build -o brainsait-cli ./cmd/brainsait/main.go` |
| Install CLI | `make install-cli` |
| Setup Apple Bridge | `make install-bridge` |
| Full macOS setup | `make install-mac` |
| Test Apple Bridge | `make bridge-test` |
| Run tests | `make test` or `go test ./...` |
| View logs | `make bridge-logs` |

## File Purposes

### Setup & Documentation
- **MAC_SETUP.md** — Comprehensive guide covering all setup scenarios
- **CLAUDE_DESKTOP_SETUP.md** — Quick start specifically for Claude Desktop/Code
- **CLAUDE.md** — This context file for Claude

### Automation
- **scripts/mac-setup.sh** — Interactive/automated macOS setup
- **Makefile** — Common development and setup tasks

### Apple Bridge
- **connectors/apple-native/README.md** — Bridge-specific documentation
- **connectors/apple-native/scripts/install.sh** — launchd agent installer
- **connectors/apple-native/scripts/com.brainsait.apple-bridge.plist** — launchd config template

## Testing

### Test Apple Bridge
```bash
# With MCP Inspector (interactive GUI)
make bridge-test

# Verify HTTP endpoint (if running in HTTP mode)
curl -H "Authorization: Bearer $APPLE_BRIDGE_TOKEN" http://127.0.0.1:8848/mcp
```

### Test CLI
```bash
brainsait-cli --help
brainsait-cli chat
```

## Troubleshooting Guide

See `MAC_SETUP.md` section "Troubleshooting" for common issues:
- Permission denied errors
- Module not found
- Token not accepted
- Shortcut not running

## Performance Notes

- **Apple Bridge stdio mode:** Very low latency, only for Claude Desktop/Code
- **Apple Bridge HTTP mode:** ~100ms overhead + tunnel latency
- **Shortcut execution:** Depends on shortcut complexity, 120s default timeout
- **Large context:** CLI handles up to 200k tokens via Claude API

## Security Considerations

1. **API Keys** — Store in environment, never commit to repo
2. **Tokens** — APPLE_BRIDGE_TOKEN should be unique and kept secret
3. **Allowlists** — Use APPLE_BRIDGE_ALLOWED_SHORTCUTS in production
4. **AppleScript** — Disable by default (APPLE_BRIDGE_ALLOW_APPLESCRIPT=0)
5. **Tunnels** — Use Cloudflare Access + Named Tunnels for production

## CI/CD Considerations

- Build requires Go 1.21+
- Tests run on macOS (mock non-macOS CLIs)
- Python tests via pytest
- GH Actions ready for auto-release

## Contributing

1. Create a feature branch from `main`
2. Make changes and test locally
3. Update relevant documentation (MAC_SETUP.md, CLAUDE_DESKTOP_SETUP.md)
4. Commit with clear messages
5. Open PR with description of changes
6. Merge after review

## Related Docs

- **README.md** — Project overview
- **MAC_SETUP.md** — Full macOS setup (all scenarios)
- **CLAUDE_DESKTOP_SETUP.md** — Claude Desktop/Code quick start
- **connectors/apple-native/README.md** — Apple Bridge details
- **Makefile** — Development tasks

## Questions for Claude

When working in this repo, ask yourself:
- ✅ Is the change documented in MAC_SETUP.md or CLAUDE_DESKTOP_SETUP.md?
- ✅ Does the change work on macOS 12+?
- ✅ Are Python and Go code tested locally?
- ✅ Does the change require updating the launchd template?
- ✅ Is the Makefile updated with new common tasks?

---

**Last Updated:** 2026-08-24
**Branch:** claude/mac-setup-4vg7yk
