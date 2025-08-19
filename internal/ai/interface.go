package ai

import "context"

type AIClient interface {
	GenerateCode(ctx context.Context, prompt string, codeContext string) (*ClaudeResponse, error)
}
