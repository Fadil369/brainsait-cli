#!/bin/bash
# mac-setup.sh - Automated BrainSAIT CLI setup for macOS
#
# Usage:
#   bash scripts/mac-setup.sh              # Interactive setup
#   bash scripts/mac-setup.sh --quick      # Skip prompts, install everything
#   bash scripts/mac-setup.sh --help       # Show this message

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPLE_BRIDGE_DIR="$REPO_ROOT/connectors/apple-native"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helpers
log_info() { echo -e "${BLUE}ℹ${NC} $*"; }
log_success() { echo -e "${GREEN}✅${NC} $*"; }
log_warning() { echo -e "${YELLOW}⚠️${NC} $*"; }
log_error() { echo -e "${RED}❌${NC} $*"; exit 1; }
log_step() { echo -e "\n${BLUE}→${NC} $*"; }

# Arguments
QUICK_MODE=false
if [[ "$1" == "--quick" ]]; then
    QUICK_MODE=true
elif [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    cat << 'EOF'
BrainSAIT CLI: macOS Setup

Usage:
  bash scripts/mac-setup.sh              # Interactive setup
  bash scripts/mac-setup.sh --quick      # Automatic setup (skip prompts)
  bash scripts/mac-setup.sh --help       # Show this help

The setup includes:
  1. Check prerequisites (Go, Python, uv)
  2. Build BrainSAIT CLI executable
  3. Install Apple Bridge (MCP connector)
  4. Configure Claude Desktop (if present)
  5. Optional: Setup launchd agent for remote use

For full documentation, see: MAC_SETUP.md
EOF
    exit 0
fi

# Check if running on macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    log_error "This script must run on macOS"
fi

log_info "BrainSAIT CLI macOS Setup"
log_step "Checking prerequisites..."

# Check Homebrew
if ! command -v brew &> /dev/null; then
    log_warning "Homebrew not found"
    if [[ "$QUICK_MODE" != "true" ]]; then
        read -p "Install Homebrew? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_step "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
    else
        log_info "Skipping Homebrew (use 'brew install homebrew' to install)"
    fi
fi

# Check Go
if ! command -v go &> /dev/null; then
    log_warning "Go not installed"
    if [[ "$QUICK_MODE" != "true" ]]; then
        read -p "Install Go via Homebrew? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_step "Installing Go..."
            brew install go@1.21
        fi
    else
        log_info "Installing Go..."
        brew install -q go@1.21 2>/dev/null || log_warning "Go installation skipped"
    fi
fi

# Verify Go
if ! command -v go &> /dev/null; then
    log_error "Go is required but not installed. Install with: brew install go"
fi
log_success "Go $(go version | awk '{print $3}')"

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
fi
log_success "Python $(python3 --version | awk '{print $2}')"

# Check/Install uv
if ! command -v uv &> /dev/null; then
    log_warning "uv (Python package manager) not found"
    if [[ "$QUICK_MODE" != "true" ]]; then
        read -p "Install uv via Homebrew? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_step "Installing uv..."
            brew install uv
        fi
    else
        log_step "Installing uv..."
        brew install -q uv 2>/dev/null || log_warning "uv installation skipped"
    fi
fi

if ! command -v uv &> /dev/null; then
    log_warning "uv not available. Apple Bridge setup will use pip instead."
    UV_CMD="python3 -m pip"
else
    UV_CMD="uv pip"
    log_success "uv $(uv --version)"
fi

# Check Git
if ! command -v git &> /dev/null; then
    log_error "Git is required but not installed"
fi
log_success "Git installed"

log_step "Building BrainSAIT CLI..."

# Build CLI
if ! go build -o brainsait-cli ./cmd/brainsait/main.go 2>/dev/null; then
    log_warning "Failed to build from ./cmd/brainsait/main.go, trying ./main.go"
    if ! go build -o brainsait-cli ./main.go 2>/dev/null; then
        log_error "Failed to build BrainSAIT CLI. Check if main.go exists."
    fi
fi
log_success "Built brainsait-cli"

# Install CLI to PATH
log_step "Installing CLI to PATH..."
if ! sudo mv brainsait-cli /usr/local/bin/ 2>/dev/null; then
    log_warning "Failed to install with sudo, trying without"
    if [[ -w /usr/local/bin ]]; then
        mv brainsait-cli /usr/local/bin/
    else
        log_error "Cannot write to /usr/local/bin. Try: sudo chown -R $(whoami) /usr/local/bin"
    fi
fi
chmod +x /usr/local/bin/brainsait-cli
log_success "CLI installed at /usr/local/bin/brainsait-cli"

# Verify CLI
if ! brainsait-cli --version &>/dev/null; then
    log_warning "CLI build may need verification. Ensure ./main.go has a --version flag"
fi

log_step "Setting up Apple Bridge (MCP connector)..."

# Setup Python venv for Apple Bridge
cd "$APPLE_BRIDGE_DIR"
if [[ -d ".venv" ]]; then
    log_info "Virtual environment already exists"
else
    log_info "Creating Python virtual environment..."
    if command -v uv &> /dev/null; then
        uv venv --allow-existing > /dev/null
    else
        python3 -m venv .venv
    fi
fi

# Activate venv and install
log_info "Installing Apple Bridge package..."
if command -v uv &> /dev/null; then
    uv pip install -q -e . 2>/dev/null || log_warning "uv pip install had issues"
else
    source .venv/bin/activate 2>/dev/null || true
    pip install -q -e . 2>/dev/null || log_warning "pip install had issues"
fi

log_success "Apple Bridge installed"

# Check for Claude Desktop
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [[ -f "$CLAUDE_CONFIG" ]]; then
    log_step "Found Claude Desktop configuration"

    if [[ "$QUICK_MODE" != "true" ]]; then
        read -p "Update Claude Desktop config to add Apple Bridge? (y/n) " -n 1 -r
        echo
        SHOULD_UPDATE_CLAUDE=$REPLY
    else
        SHOULD_UPDATE_CLAUDE="y"
    fi

    if [[ $SHOULD_UPDATE_CLAUDE =~ ^[Yy]$ ]]; then
        log_info "Updating Claude Desktop configuration..."

        # Create backup
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%s)"
        log_info "Backed up to $CLAUDE_CONFIG.backup.*"

        # Use Python to safely update JSON
        python3 << PYTHON_EOF
import json
import os

config_path = "$CLAUDE_CONFIG"
bridge_dir = "$APPLE_BRIDGE_DIR"

with open(config_path, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['apple-bridge'] = {
    "command": "uv",
    "args": [
        "--directory",
        bridge_dir,
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

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"✓ Updated: {config_path}")
PYTHON_EOF

        log_success "Claude Desktop config updated"
        log_info "Restart Claude Desktop to activate Apple Bridge"
    fi
else
    log_warning "Claude Desktop not found"
fi

# Optional: Setup launchd agent
if [[ "$QUICK_MODE" != "true" ]]; then
    log_step "Optional: Setup launchd agent (runs at login)"
    read -p "Install launchd agent for remote use? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_step "Running launchd setup..."
        bash "$APPLE_BRIDGE_DIR/scripts/install.sh"
    fi
fi

# Summary
log_step "Setup Complete! 🎉"
log_success "BrainSAIT CLI installed"
log_success "Apple Bridge installed"

echo ""
echo "Next steps:"
echo "  1. For Claude Desktop:"
echo "     → Restart Claude Desktop to enable Apple Bridge"
echo "     → Try 'list_shortcuts' to test"
echo ""
echo "  2. For Claude Code:"
echo "     → Run: claude mcp add apple-bridge -- uv --directory $APPLE_BRIDGE_DIR run brainsait-apple-bridge"
echo ""
echo "  3. Configuration:"
echo "     → Set ANTHROPIC_API_KEY in ~/.zshrc or ~/.bash_profile"
echo "     → See MAC_SETUP.md for full documentation"
echo ""
echo "  4. Test:"
echo "     → brainsait-cli --help"
echo "     → brainsait-cli chat"
echo ""
