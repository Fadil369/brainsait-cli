package ai

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
)

// ClaudeClient implements the AIClient interface for the Anthropic Claude API.
var _ AIClient = (*ClaudeClient)(nil)

type ClaudeClient struct {
	apiKey     string
	baseURL    string
	httpClient *http.Client
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ClaudeRequest struct {
	Model     string    `json:"model"`
	MaxTokens int       `json:"max_tokens"`
	Messages  []Message `json:"messages"`
	Stream    bool      `json:"stream,omitempty"`
}

type ClaudeResponse struct {
	Content []struct {
		Text string `json:"text"`
	} `json:"content"`
}

func NewClaudeClient(apiKey string) *ClaudeClient {
	return &ClaudeClient{
		apiKey:     apiKey,
		baseURL:    "https://api.anthropic.com/v1",
		httpClient: &http.Client{},
	}
}

func (c *ClaudeClient) GenerateCode(ctx context.Context, prompt string, codeContext string) (*ClaudeResponse, error) {
	messages := []Message{
		{Role: "system", Content: buildSystemPrompt()},
		{Role: "user", Content: fmt.Sprintf("Context:\n%s\n\nRequest:\n%s", codeContext, prompt)},
	}

	req := ClaudeRequest{
		Model:     "claude-3-sonnet-20240229", // Corrected model name
		MaxTokens: 4096,
		Messages:  messages,
		Stream:    false, // Assuming non-streaming for this implementation
	}

	return c.sendRequest(ctx, req)
}

func (c *ClaudeClient) sendRequest(ctx context.Context, payload ClaudeRequest) (*ClaudeResponse, error) {
	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/messages", bytes.NewBuffer(jsonPayload))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-api-key", c.apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var claudeResp ClaudeResponse
	if err := json.NewDecoder(resp.Body).Decode(&claudeResp); err != nil {
		return nil, err
	}

	return &claudeResp, nil
}

func buildSystemPrompt() string {
	return `You are BrainSAIT Code Assistant, an AI agent specialized in:
- Writing clean, production-ready code
- Following best practices and design patterns
- Providing Arabic/English documentation when needed
- Integrating with healthcare and automation systems
- Supporting deployment on macOS, Docker, and Cloudflare

Always provide:
1. Complete, runnable code
2. Clear explanations
3. Error handling
4. Testing suggestions
5. Deployment considerations`
}
