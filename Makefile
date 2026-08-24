.PHONY: help install install-mac install-cli install-bridge setup test clean help-mac

# Default goal
help:
	@echo "BrainSAIT CLI - Available targets:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install-mac       Run full macOS setup (interactive)"
	@echo "  make install-mac-quick Run full macOS setup (no prompts)"
	@echo "  make install-cli       Build and install CLI only"
	@echo "  make install-bridge    Install Apple Bridge only"
	@echo ""
	@echo "Development:"
	@echo "  make build             Build brainsait-cli binary"
	@echo "  make test              Run tests"
	@echo "  make clean             Remove build artifacts"
	@echo ""
	@echo "Apple Bridge (MCP):"
	@echo "  make bridge-venv       Create/update Python venv"
	@echo "  make bridge-install    Install bridge into venv"
	@echo "  make bridge-test       Test bridge with MCP inspector"
	@echo "  make bridge-logs       Show latest bridge logs"
	@echo "  make bridge-uninstall  Remove launchd agent"
	@echo ""
	@echo "Documentation:"
	@echo "  make help-mac          Show macOS setup help"
	@echo "  make docs              Open documentation"

# macOS Full Setup
install-mac:
	@echo "Starting BrainSAIT CLI macOS setup..."
	@bash scripts/mac-setup.sh

install-mac-quick:
	@echo "Running macOS setup (quick mode, no prompts)..."
	@bash scripts/mac-setup.sh --quick

# CLI Installation
install-cli: build
	@echo "Installing CLI to /usr/local/bin..."
	@if [ -w /usr/local/bin ]; then \
		mv brainsait-cli /usr/local/bin/; \
	else \
		sudo mv brainsait-cli /usr/local/bin/; \
	fi
	@chmod +x /usr/local/bin/brainsait-cli
	@echo "✅ CLI installed: brainsait-cli"

build:
	@echo "Building brainsait-cli..."
	@if [ -f cmd/brainsait/main.go ]; then \
		go build -o brainsait-cli ./cmd/brainsait/main.go; \
	elif [ -f main.go ]; then \
		go build -o brainsait-cli ./main.go; \
	else \
		echo "Error: main.go not found"; exit 1; \
	fi
	@echo "✅ Built: ./brainsait-cli"

# Apple Bridge Setup
install-bridge: bridge-venv bridge-install

bridge-venv:
	@echo "Setting up Python virtual environment..."
	@cd connectors/apple-native && \
		if command -v uv > /dev/null; then \
			uv venv --allow-existing; \
		else \
			python3 -m venv .venv; \
		fi
	@echo "✅ Virtual environment ready"

bridge-install: bridge-venv
	@echo "Installing Apple Bridge package..."
	@cd connectors/apple-native && \
		if command -v uv > /dev/null; then \
			uv pip install -e .; \
		else \
			. .venv/bin/activate && pip install -e .; \
		fi
	@echo "✅ Apple Bridge installed"

bridge-test: bridge-install
	@echo "Testing Apple Bridge with MCP inspector..."
	@command -v npx > /dev/null || (echo "Node.js required. Install with: brew install node"; exit 1)
	@cd connectors/apple-native && \
		npx @modelcontextprotocol/inspector uv run brainsait-apple-bridge

bridge-logs:
	@echo "Apple Bridge logs:"
	@if [ -f /tmp/brainsait-apple-bridge.log ]; then \
		tail -20 /tmp/brainsait-apple-bridge.log; \
	else \
		echo "No logs found. Is the bridge running?"; \
	fi

bridge-uninstall:
	@echo "Uninstalling launchd agent..."
	@launchctl unload ~/Library/LaunchAgents/com.brainsait.apple-bridge.plist 2>/dev/null || true
	@rm -f ~/Library/LaunchAgents/com.brainsait.apple-bridge.plist
	@echo "✅ Launchd agent removed"

# Testing
test:
	@echo "Running tests..."
	@if [ -f "go.mod" ]; then \
		go test -v ./...; \
	fi
	@if [ -d "connectors/apple-native/tests" ]; then \
		cd connectors/apple-native && python3 -m pytest tests/ -v; \
	fi

# Cleanup
clean:
	@echo "Cleaning up..."
	@rm -f brainsait-cli
	@rm -f connectors/apple-native/brainsait-apple-bridge
	@echo "✅ Cleaned"

# Documentation
help-mac:
	@cat MAC_SETUP.md

docs:
	@if command -v open > /dev/null; then \
		open MAC_SETUP.md; \
	else \
		echo "See MAC_SETUP.md for full documentation"; \
	fi

# Phony targets
.PHONY: install-mac install-mac-quick install-cli install-bridge bridge-venv bridge-install bridge-test bridge-logs bridge-uninstall test clean help help-mac docs
