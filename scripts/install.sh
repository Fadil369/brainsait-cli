#!/bin/bash
# install.sh

set -e

REPO="brainsait/brainsait-cli"
INSTALL_DIR="/usr/local/bin"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $ARCH in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Download latest release
LATEST=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | cut -d'"' -f4)
URL="https://github.com/$REPO/releases/download/$LATEST/brainsait-cli-$OS-$ARCH"

echo "📥 Downloading BrainSAIT CLI $LATEST for $OS/$ARCH..."
curl -L "$URL" -o brainsait-cli

chmod +x brainsait-cli
sudo mv brainsait-cli "$INSTALL_DIR/"

echo "✅ BrainSAIT CLI installed successfully!"
echo "🚀 Run 'brainsait-cli --help' to get started"
