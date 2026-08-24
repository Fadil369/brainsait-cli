# BrainSAIT CLI: macOS Setup Guide

Complete setup instructions for installing and configuring BrainSAIT CLI on macOS.

## Overview

BrainSAIT CLI is an AI-powered command-line assistant with native integration to Apple Shortcuts and Automator through the **Apple Bridge MCP connector**. This guide covers:

- Installing BrainSAIT CLI
- Setting up the Apple Bridge for local use (Claude Desktop/Code)
- Configuring for remote use (claude.ai Custom Connectors)

## Prerequisites

### Required
- **macOS 12.0 or later** (for the `shortcuts` CLI)
- **Homebrew** (for easy package management)
- **Python 3.10+**
- **Git**

### Optional but Recommended
- **Cloudflare Wrangler** (for tunneling to claude.ai)
- **Docker** (for code execution features)

## Quick Start (5 minutes)

### 1. Install Homebrew (if needed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Run the automated setup
```bash
# Clone the repo (if not already cloned)
git clone https://github.com/Fadil369/brainsait-cli.git
cd brainsait-cli

# Run the setup script
bash scripts/mac-setup.sh
```

This will:
- Install `uv` (Python package manager)
- Build the BrainSAIT CLI
- Set up the Apple Bridge
- Configure Claude Desktop integration (if detected)

---

## Detailed Installation

### Step 1: Install Dependencies

#### Using Homebrew (Recommended)
```bash
# Install uv (fast Python package manager)
brew install uv

# Install Go (if not present)
brew install go@1.21

# Optional: Install Docker for code execution
brew install docker
```

#### Using asdf (Alternative)
```bash
asdf plugin add python
asdf plugin add go
asdf install
```

### Step 2: Build BrainSAIT CLI

```bash
cd /path/to/brainsait-cli

# Build the Go CLI
go build -o brainsait-cli ./cmd/brainsait/main.go

# Add to PATH
sudo mv brainsait-cli /usr/local/bin/
chmod +x /usr/local/bin/brainsait-cli

# Verify installation
brainsait-cli --version
```

### Step 3: Set Up Apple Bridge (Local - stdio)

The Apple Bridge allows Claude Desktop and Claude Code to control Apple Shortcuts and Automator.

#### 3a. Install Python Dependencies

```bash
cd connectors/apple-native
uv venv
source .venv/bin/activate
uv pip install -e .
```

#### 3b. Grant Automation Permissions

Open **System Settings → Privacy & Security → Automation** and allow:
- Your terminal app (or iTerm2/Alacritty)
- To control "Shortcuts Events"
- To control the apps that your shortcuts run

**Note:** You may need to allow each app individually when running shortcuts.

#### 3c. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-bridge": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/brainsait-cli/connectors/apple-native",
        "run",
        "brainsait-apple-bridge",
        "--transport",
        "stdio"
      ],
      "env": {
        "APPLE_BRIDGE_ALLOWED_SHORTCUTS": "",
        "APPLE_BRIDGE_ALLOW_APPLESCRIPT": "0"
      }
    }
  }
}
```

Replace `/path/to/brainsait-cli` with the actual path (use `pwd` to get it).

Restart Claude Desktop to activate.

#### 3d. Configure Claude Code (Alternative)

```bash
cd /path/to/brainsait-cli
claude mcp add apple-bridge -- uv --directory $(pwd)/connectors/apple-native run brainsait-apple-bridge
```

---

## Advanced: Remote Setup (claude.ai Custom Connectors)

If you want to use the Apple Bridge from **claude.ai** (not just Claude Desktop):

### Step 1: Install as launchd Agent (Runs at Login)

```bash
cd /path/to/brainsait-cli/connectors/apple-native
bash scripts/install.sh
```

This will:
- Create a launch agent that runs at login
- Generate a secure token
- Output the endpoint and connection details

**Output example:**
```
BrainSAIT Apple Bridge installed and running.

  Endpoint : http://127.0.0.1:8848/mcp
  Token    : a1b2c3d4e5f6...
  Logs     : /tmp/brainsait-apple-bridge.log

Next, expose it with cloudflared tunnel:
  cloudflared tunnel --url http://127.0.0.1:8848
```

### Step 2: Create a Tunnel

Install and run Cloudflare Tunnel:

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Create a tunnel to your local server
cloudflared tunnel --url http://127.0.0.1:8848
```

You'll get a URL like: `https://xyz-abc-123.trycloudflare.com`

### Step 3: Add to claude.ai Custom Connectors

1. Go to **claude.ai → Settings → Connectors → Add custom connector**
2. Set the **URL** to:
   ```
   https://xyz-abc-123.trycloudflare.com/mcp?token=YOUR_TOKEN
   ```
3. Name it "Apple Bridge" and save

Now Claude can run your Shortcuts and Automator workflows from claude.ai!

---

## Configuration & Environment Variables

### Apple Bridge Settings

Set these in your shell profile (`~/.zshrc`, `~/.bash_profile`) or in the launchd agent:

```bash
# Restrict which shortcuts can run (comma-separated names)
export APPLE_BRIDGE_ALLOWED_SHORTCUTS="Fetch Email,Send Message"

# Allow AppleScript execution (default: disabled)
export APPLE_BRIDGE_ALLOW_APPLESCRIPT=1

# Custom Automator workflow directories
export APPLE_BRIDGE_WORKFLOW_DIRS="$HOME/Library/Services,$HOME/Documents/Automator"

# Timeout per run (seconds, default: 120, max: 600)
export APPLE_BRIDGE_TIMEOUT=300

# HTTP server host/port
export APPLE_BRIDGE_HOST=127.0.0.1
export APPLE_BRIDGE_PORT=8848
```

### BrainSAIT CLI Configuration

Set your AI provider credentials:

```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# For OpenAI (optional)
export OPENAI_API_KEY="sk-..."

# Default model (optional)
export BRAINSAIT_MODEL="claude-3-5-sonnet-20241022"
```

Add these to your shell profile for persistence.

---

## Verification

### Test Local Setup (Claude Desktop/Code)

1. Open Claude Desktop or Claude Code
2. The Apple Bridge should appear in the MCP list
3. Try: `list_shortcuts` to see your Shortcuts
4. Run a test shortcut from Claude

### Test Remote Setup (claude.ai)

1. Ensure the tunnel is running (`cloudflared tunnel --url ...`)
2. Go to claude.ai and select the Apple Bridge custom connector
3. Try the same commands

### Debug

Check logs:
```bash
# Local mode (stdio)
# Logs appear in Claude's console

# Remote mode (HTTP)
tail -f /tmp/brainsait-apple-bridge.log
tail -f /tmp/brainsait-apple-bridge.err
```

Verify the HTTP endpoint:
```bash
TOKEN="your_token_here"
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8848/mcp
```

---

## Troubleshooting

### Permission Denied Errors

**Problem:** "Shortcuts Events: not authorized"

**Solution:**
1. Open **System Settings → Privacy & Security → Automation**
2. Find your terminal app and allow it
3. Allow the target apps (Mail, Finder, etc.) that shortcuts control
4. Restart terminal

### Module Not Found

**Problem:** `ModuleNotFoundError: No module named 'brainsait_apple_bridge'`

**Solution:**
```bash
cd connectors/apple-native
uv pip install -e .
```

### Token Not Accepted

**Problem:** "Token authentication failed"

**Solution:**
1. Retrieve the token from the launchd agent:
   ```bash
   /usr/libexec/PlistBuddy -c 'Print :EnvironmentVariables:APPLE_BRIDGE_TOKEN' \
     ~/Library/LaunchAgents/com.brainsait.apple-bridge.plist
   ```
2. Use it in the claude.ai custom connector URL
3. Or, set a new token manually:
   ```bash
   export APPLE_BRIDGE_TOKEN="$(openssl rand -hex 24)"
   brainsait-apple-bridge --transport http --port 8848
   ```

### Shortcut Not Running

**Problem:** "Shortcut execution failed" or "Permission denied"

**Solution:**
1. Verify the shortcut name is correct: `list_shortcuts`
2. Check if it's in the allowlist: `echo $APPLE_BRIDGE_ALLOWED_SHORTCUTS`
3. Run directly in Shortcuts app to verify it works
4. Check logs for details

---

## Next Steps

### Use BrainSAIT CLI
```bash
# Interactive chat with project context
brainsait-cli chat

# Generate code
brainsait-cli code "create a function to sort an array"

# Review code
brainsait-cli review src/main.go

# Deploy
brainsait-cli deploy --platform cloudflare --env production
```

### Create Shortcuts for Claude

Use Claude to help you create Shortcuts that are useful:
- Fetch daily information
- Send notifications
- Process files
- Control your Mac
- Automate workflows

Claude can then run and automate these for you!

---

## Security Best Practices

1. **Keep tokens secret** — Don't commit `APPLE_BRIDGE_TOKEN` to git
2. **Use allowlists** — Restrict shortcuts via `APPLE_BRIDGE_ALLOWED_SHORTCUTS`
3. **Monitor logs** — Check `/tmp/brainsait-apple-bridge.log` regularly
4. **Scope tunnels** — Use Cloudflare Access or firewall rules for production
5. **Rotate tokens** — Regenerate tokens periodically with `openssl rand -hex 24`

---

## Uninstall

### Remove Local Setup
```bash
rm /usr/local/bin/brainsait-cli
rm -rf connectors/apple-native/.venv
```

### Remove launchd Agent
```bash
launchctl unload ~/Library/LaunchAgents/com.brainsait.apple-bridge.plist
rm ~/Library/LaunchAgents/com.brainsait.apple-bridge.plist
```

### Remove Claude Desktop Integration
Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and remove the `apple-bridge` section.

---

## Support & Resources

- **Repository:** https://github.com/Fadil369/brainsait-cli
- **Issues:** https://github.com/Fadil369/brainsait-cli/issues
- **Apple Bridge Docs:** See `connectors/apple-native/README.md`
- **Go Docs:** https://golang.org/doc
- **MCP Specification:** https://modelcontextprotocol.io/

---

## License

MIT License — See LICENSE file
