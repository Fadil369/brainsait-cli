# BrainSAIT CLI: AI-Powered Code Assistant

## Project Overview

The BrainSAIT CLI is an intelligent command-line interface tool designed to assist developers with automated coding tasks using advanced AI models. Built with Go, it provides features for interactive coding sessions, code generation, code review, and deployment, aiming to streamline the development workflow.

## Features

*   **Interactive Chat Sessions:** Engage in real-time coding conversations with AI, with automatic project context analysis.
*   **Code Generation:** Generate code snippets or full components based on natural language prompts.
*   **Code Review:** Get AI-powered reviews for your code files, identifying potential issues and suggesting improvements.
*   **Deployment Simulation:** Simulate deployments to various platforms (e.g., Cloudflare Workers).
*   **Project Context Management:** Automatically analyzes your project structure, files, and dependencies to provide relevant context to the AI.
*   **File Watching:** Monitors project files for changes and updates the AI's context in real-time.
*   **Pluggable AI Services:** Easily switch between different AI providers (e.g., Anthropic Claude, OpenAI GPT) via configuration.
*   **Secure Code Execution:** Executes generated code in isolated Docker containers for safety.

## Architecture Overview

The CLI code agent consists of several key components:

*   **CLI Interface:** Handles user input and commands using Cobra.
*   **Command Parser:** Parses flags and options for various commands.
*   **Context Manager:** Tracks conversation history, maintains project state, and handles file references.
*   **AI API Client:** Connects to LLM providers (Claude, GPT) and manages requests/responses.
*   **Code Executor:** Provides safe code execution in sandboxed Docker environments.
*   **File System Handler:** Manages file operations within the project.
*   **Project Analyzer:** Analyzes codebase structure, dependencies, and file relationships.
*   **Response Formatter:** Formats AI responses for clear presentation in the CLI.

## Technology Stack

*   **Language:** Go
*   **CLI Framework:** Cobra
*   **AI APIs:** Anthropic Claude, OpenAI GPT (pluggable)
*   **File System Monitoring:** fsnotify
*   **Containerization:** Docker (for code execution)

## Installation

### Prerequisites

*   Go (1.18 or higher)
*   Docker (for code execution features)
*   Git

### From Source

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:Fadil369/brainsait-cli.git
    cd brainsait-cli
    ```
2.  **Build the executable:**
    ```bash
    go build -o brainsait-cli ./main.go
    ```
3.  **Add to your PATH (optional):**
    Move the `brainsait-cli` executable to a directory in your system's PATH (e.g., `/usr/local/bin`).
    ```bash
    sudo mv brainsait-cli /usr/local/bin/
    ```

### Using the Install Script (Linux/macOS)

```bash
curl -sL https://raw.githubusercontent.com/Fadil369/brainsait-cli/main/scripts/install.sh | bash
```

## Configuration

The BrainSAIT CLI requires an API key for the AI service you wish to use. Set the appropriate environment variable before running the CLI.

*   **Anthropic Claude:** `ANTHROPIC_API_KEY`
*   **OpenAI GPT:** `OPENAI_API_KEY`

Example:
```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
export OPENAI_API_KEY="your_openai_api_key_here" # If using OpenAI
```

## Usage

### General Commands

```bash
brainsait --help
brainsait chat --help
brainsait code --help
brainsait review --help
brainsait deploy --help
```

### Interactive Chat Session

Start an interactive coding session. The CLI will analyze your project context and send it to the AI.

```bash
brainsait chat
```

You can specify the AI model to use:

```bash
brainsait chat --model claude-3-sonnet-20240229
brainsait chat --model gpt-4
```

### Generate Code

Generate code based on a prompt.

```bash
brainsait code "create a simple Go function to calculate factorial"
```

### Code Review

Get an AI-powered review for a specific code file.

```bash
brainsait review src/main.go
```

### Deploy (Simulation)

Simulate a deployment to a specified platform and environment.

```bash
brainsait deploy --platform cloudflare --env production
```

## Native Connectors

### Apple Shortcuts ↔ Automator Bridge (MCP)

The repo ships a native MCP connector ([`connectors/apple-native`](connectors/apple-native/))
that bridges Apple Shortcuts and Automator to Claude — usable locally from Claude
Desktop/Claude Code (stdio) or from claude.ai as a **Custom Connector** (streamable
HTTP behind a tunnel). It can list and run Shortcuts, run and introspect Automator
workflows, and chain both apps into a single pipeline with `run_bridge_pipeline`.

```bash
# Local (stdio, for Claude Desktop / Claude Code)
brainsait connector apple

# Remote (HTTP, for claude.ai Custom Connectors)
export APPLE_BRIDGE_TOKEN="$(openssl rand -hex 24)"
brainsait connector apple --transport http --port 8848
cloudflared tunnel --url http://127.0.0.1:8848
```

See [connectors/apple-native/README.md](connectors/apple-native/README.md) for
setup, security model (allowlists, AppleScript gate, token auth), and the launchd
installer.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.
