#!/usr/bin/env bash
# Install the BrainSAIT Apple Bridge as a launchd agent (HTTP mode, runs at login).
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This installer must run on macOS." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_TEMPLATE="$SCRIPT_DIR/com.brainsait.apple-bridge.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.brainsait.apple-bridge.plist"

UV_PATH="$(command -v uv || true)"
if [[ -z "$UV_PATH" ]]; then
    echo "uv is required (https://docs.astral.sh/uv). Install with: brew install uv" >&2
    exit 1
fi

# Reuse an existing token if the agent was installed before; otherwise mint one.
TOKEN="${APPLE_BRIDGE_TOKEN:-}"
if [[ -z "$TOKEN" && -f "$PLIST_DEST" ]]; then
    TOKEN="$(/usr/libexec/PlistBuddy -c 'Print :EnvironmentVariables:APPLE_BRIDGE_TOKEN' "$PLIST_DEST" 2>/dev/null || true)"
fi
if [[ -z "$TOKEN" ]]; then
    TOKEN="$(openssl rand -hex 24)"
fi

echo "Installing Python package..."
(cd "$BRIDGE_DIR" && uv venv --allow-existing >/dev/null && uv pip install -q -e .)

mkdir -p "$HOME/Library/LaunchAgents"
sed -e "s|__UV_PATH__|$UV_PATH|g" \
    -e "s|__BRIDGE_DIR__|$BRIDGE_DIR|g" \
    -e "s|__TOKEN__|$TOKEN|g" \
    "$PLIST_TEMPLATE" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

cat <<EOF

BrainSAIT Apple Bridge installed and running.

  Endpoint : http://127.0.0.1:8848/mcp
  Token    : $TOKEN
  Logs     : /tmp/brainsait-apple-bridge.log

Next, expose it for claude.ai Custom Connectors:

  cloudflared tunnel --url http://127.0.0.1:8848

Then add this URL in claude.ai -> Settings -> Connectors -> Add custom connector:

  https://<tunnel-host>/mcp?token=$TOKEN

To uninstall: launchctl unload "$PLIST_DEST" && rm "$PLIST_DEST"
EOF
