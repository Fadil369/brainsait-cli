# BrainSAIT Apple Bridge: Claude Desktop/Code Setup

Quick setup guide for using BrainSAIT Apple Bridge with Claude Desktop or Claude Code.

## What is Apple Bridge?

Apple Bridge is an MCP (Model Context Protocol) connector that lets Claude:
- **List** your Apple Shortcuts
- **Run** Shortcuts with input/output
- **Control** Automator workflows
- **Chain** Shortcuts → Automator → AppleScript in pipelines

This means Claude can automate your Mac directly!

## Prerequisites

- **macOS 12+** (for the `shortcuts` CLI)
- **Python 3.10+**
- **Claude Desktop** or **Claude Code** installed
- **Terminal access**

## Installation (5 minutes)

### Option 1: Automated Setup (Recommended)

```bash
cd /path/to/brainsait-cli
bash scripts/mac-setup.sh
```

Follow the prompts. The script will:
1. Build BrainSAIT CLI
2. Install Apple Bridge
3. Configure Claude Desktop automatically

Then restart Claude Desktop — done!

### Option 2: Manual Setup

#### 1. Clone the repository
```bash
git clone https://github.com/Fadil369/brainsait-cli.git
cd brainsait-cli
```

#### 2. Install Python dependencies
```bash
cd connectors/apple-native
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### 3. Grant permissions
- Open **System Settings → Privacy & Security → Automation**
- Allow your **Terminal app** (or iTerm2/Alacritty) to control Shortcuts Events
- Allow the target apps (Mail, Finder, etc.) that Shortcuts will control

#### 4. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-bridge": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/brainsait-cli/connectors/apple-native",
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

Replace `/absolute/path/to/brainsait-cli` with the actual path. Get it with:
```bash
cd /path/to/brainsait-cli && pwd
```

#### 5. Restart Claude Desktop

Close and reopen Claude Desktop. The Apple Bridge should now be available!

---

## For Claude Code Users

Instead of editing the JSON, run:

```bash
cd /path/to/brainsait-cli
claude mcp add apple-bridge -- uv --directory $(pwd)/connectors/apple-native run brainsait-apple-bridge
```

---

## First Test

In Claude Desktop/Code, try:

```
Can you list my Shortcuts?
```

Claude should respond with a list of your Shortcuts. Example:

> I found 3 Shortcuts:
> - "Fetch Email"
> - "Send Message"
> - "Get Weather"

If this works, you're all set! 🎉

---

## Using Apple Bridge

### Simple Shortcut Run

**You:** "Run my 'Get Weather' shortcut"

**Claude:**
```
I'll run your "Get Weather" shortcut.
```

(Claude runs it and shows output)

### With Input

**You:** "Run 'Send Message' with 'Hello, World!'"

**Claude:**
- Runs the Shortcut
- Passes "Hello, World!" as input
- Shows the result

### Automator Workflows

**You:** "Can you run the 'Process Files' Automator workflow?"

**Claude:**
- Lists available workflows
- Runs it
- Shows results

### Chained Pipelines

**You:** "Run 'Fetch Email' then pipe output to 'Save Report' workflow"

**Claude:**
- Runs Shortcut 1 → Shortcut 2 → Automator
- Chains outputs automatically

---

## Troubleshooting

### "Shortcuts Events: not authorized"

**Fix:**
1. Open **System Settings → Privacy & Security → Automation**
2. Find your terminal app (Terminal, iTerm2, etc.)
3. Click the checkbox to allow "Shortcuts Events"
4. Allow the specific apps (Mail, Finder, etc.) in the next dialog

### "brainsait-apple-bridge: command not found"

**Fix:**
- Use absolute path in config: `/Users/yourname/...brainsait-cli/...`
- Or install uv globally: `brew install uv`

### Config not found after restart

**Fix:**
- Close Claude completely: `cmd+Q` (not just minimize)
- Reopen Claude Desktop
- Check file saved: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json`

### Shortcut not running

**Fix:**
1. Run the Shortcut directly in **Shortcuts.app** to verify it works
2. Check the exact Shortcut name: `list_shortcuts` in Claude
3. Check allowlist: Is `APPLE_BRIDGE_ALLOWED_SHORTCUTS` restricting it?

### No output from Shortcut

**Fix:**
- Shortcut may not output text
- Check the Shortcut in **Shortcuts.app**
- Add a "Text" step at the end to return output

---

## Limitations

- ⚠️ Some Shortcuts may require user interaction (you'll see a prompt on your Mac)
- ⚠️ Shortcuts that require specific apps may fail if those apps are closed
- ⚠️ Very long-running Shortcuts may timeout (default 120 seconds)

---

## Advanced: Allow/Block Shortcuts

Restrict which Shortcuts Claude can run:

Edit the config and change:
```json
"APPLE_BRIDGE_ALLOWED_SHORTCUTS": "Shortcut One,Shortcut Two"
```

Now Claude can only run those Shortcuts.

---

## Advanced: Enable AppleScript

To let Claude run raw AppleScript (expert only!):

```json
"APPLE_BRIDGE_ALLOW_APPLESCRIPT": "1"
```

⚠️ AppleScript can do anything — use with caution!

---

## Next Steps

1. **Create useful Shortcuts** that Claude can run
   - Data fetching (email, calendar)
   - Notifications (reminders, alerts)
   - File operations
   - System automation

2. **Share ideas with Claude**
   - "Help me create a Shortcut to..."
   - Claude will guide you through Shortcuts.app

3. **Explore Automator workflows**
   - Folder actions
   - Service workflows
   - Calendar/Mail automations

---

## Support

- **Apple Bridge Docs:** See `connectors/apple-native/README.md`
- **Issues:** https://github.com/Fadil369/brainsait-cli/issues
- **MCP Spec:** https://modelcontextprotocol.io/

Happy automating! 🚀
