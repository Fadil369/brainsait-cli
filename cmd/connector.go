package cmd

import (
    "fmt"
    "os"
    "os/exec"
    "path/filepath"

    "github.com/spf13/cobra"
)

var (
    connectorTransport string
    connectorPort      int
    connectorDir       string
)

var connectorCmd = &cobra.Command{
    Use:   "connector",
    Short: "Run BrainSAIT native connectors (MCP servers)",
}

var appleConnectorCmd = &cobra.Command{
    Use:   "apple",
    Short: "Run the Apple Shortcuts <-> Automator MCP bridge",
    Long: `Starts the BrainSAIT Apple Bridge, an MCP server exposing Apple Shortcuts
and Automator to Claude.

Transports:
  stdio  for Claude Desktop / Claude Code on this Mac (default)
  http   for claude.ai custom connectors (expose via a tunnel)`,
    RunE: func(cmd *cobra.Command, args []string) error {
        dir := connectorDir
        if dir == "" {
            dir = os.Getenv("BRAINSAIT_APPLE_BRIDGE_DIR")
        }
        if dir == "" {
            // Default: connectors/apple-native next to the working directory.
            dir = filepath.Join("connectors", "apple-native")
        }
        if _, err := os.Stat(filepath.Join(dir, "pyproject.toml")); err != nil {
            return fmt.Errorf("apple bridge not found at %q — pass --dir or set BRAINSAIT_APPLE_BRIDGE_DIR", dir)
        }

        uvPath, err := exec.LookPath("uv")
        if err != nil {
            return fmt.Errorf("uv is required to run the bridge (brew install uv): %w", err)
        }

        uvArgs := []string{"--directory", dir, "run", "brainsait-apple-bridge", "--transport", connectorTransport}
        if connectorTransport == "http" {
            uvArgs = append(uvArgs, "--port", fmt.Sprintf("%d", connectorPort))
        }

        bridge := exec.Command(uvPath, uvArgs...)
        bridge.Stdin = os.Stdin
        bridge.Stdout = os.Stdout
        bridge.Stderr = os.Stderr
        bridge.Env = os.Environ()
        return bridge.Run()
    },
}

func init() {
    appleConnectorCmd.Flags().StringVar(&connectorTransport, "transport", "stdio", "transport: stdio or http")
    appleConnectorCmd.Flags().IntVar(&connectorPort, "port", 8848, "HTTP port (http transport only)")
    appleConnectorCmd.Flags().StringVar(&connectorDir, "dir", "", "path to connectors/apple-native")
    connectorCmd.AddCommand(appleConnectorCmd)
}
