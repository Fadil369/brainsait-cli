package plugins

import (
	"context"
)

type PluginInput struct {
	// Define plugin input structure
}

type PluginOutput struct {
	// Define plugin output structure
}

type Plugin interface {
	Name() string
	Version() string
	Initialize(config map[string]interface{}) error
	Execute(ctx context.Context, input *PluginInput) (*PluginOutput, error)
}
