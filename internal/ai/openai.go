package ai

import (
	"context"
	"fmt"
)

// OpenAIClient implements the AIClient interface for the OpenAI API.
var _ AIClient = (*OpenAIClient)(nil)

type OpenAIClient struct {
	apiKey string
}

func NewOpenAIClient(apiKey string) *OpenAIClient {
	return &OpenAIClient{apiKey: apiKey}
}

func (c *OpenAIClient) GenerateCode(ctx context.Context, prompt string, codeContext string) (*ClaudeResponse, error) {
	// This is a placeholder for the actual implementation
	return nil, fmt.Errorf("OpenAI client not implemented yet")
}
