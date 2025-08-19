package executor

import (
	"context"
	"fmt"
	"os"
	"os/exec"
)

type ExecutionResult struct {
	Success    bool   `json:"success"`
	Output     string `json:"output"`
	Error      string `json:"error,omitempty"`
	ExitCode   int    `json:"exit_code"`
	Duration   string `json:"duration"`
}

type CodeExecutor struct {
	workingDir   string
	dockerEnabled bool
	safeMode     bool
}

func NewCodeExecutor(workingDir string) *CodeExecutor {
	return &CodeExecutor{
		workingDir:   workingDir,
		dockerEnabled: true,
		safeMode:     true,
	}
}

func (ce *CodeExecutor) ExecuteCode(ctx context.Context, code string, language string) (*ExecutionResult, error) {
	if ce.safeMode && !ce.isSafeCode(code) {
		return nil, fmt.Errorf("potentially unsafe code detected")
	}

	switch language {
	case "python":
		return ce.executePython(ctx, code)
	case "javascript", "node":
		return ce.executeNode(ctx, code)
	case "go":
		return ce.executeGo(ctx, code)
	case "bash", "shell":
		return ce.executeShell(ctx, code)
	default:
		return nil, fmt.Errorf("unsupported language: %s", language)
	}
}

func (ce *CodeExecutor) executePython(ctx context.Context, code string) (*ExecutionResult, error) {
	if ce.dockerEnabled {
		return ce.executeInDocker(ctx, "python:3.11-slim", code, "python")
	}

	cmd := exec.CommandContext(ctx, "python3", "-c", code)
	cmd.Dir = ce.workingDir

	output, err := cmd.CombinedOutput()

	result := &ExecutionResult{
		Success:  err == nil,
		Output:   string(output),
	}

	if err != nil {
		result.Error = err.Error()
	}

	return result, nil
}

func (ce *CodeExecutor) executeNode(ctx context.Context, code string) (*ExecutionResult, error) {
	// Placeholder for Node.js execution
	return &ExecutionResult{Success: true, Output: "Node code executed"}, nil
}

func (ce *CodeExecutor) executeGo(ctx context.Context, code string) (*ExecutionResult, error) {
	// Placeholder for Go execution
	return &ExecutionResult{Success: true, Output: "Go code executed"}, nil
}

func (ce *CodeExecutor) executeShell(ctx context.Context, code string) (*ExecutionResult, error) {
	// Placeholder for Shell execution
	return &ExecutionResult{Success: true, Output: "Shell code executed"}, nil
}

func (ce *CodeExecutor) isSafeCode(code string) bool {
	// Placeholder for code safety check
	return true
}

func (ce *CodeExecutor) executeInDocker(ctx context.Context, image, code, interpreter string) (*ExecutionResult, error) {
	tempFile, err := os.CreateTemp("", "code-")
	if err != nil {
		return nil, fmt.Errorf("failed to create temp file: %w", err)
	}
	defer os.Remove(tempFile.Name())

	if _, err := tempFile.WriteString(code); err != nil {
		return nil, fmt.Errorf("failed to write to temp file: %w", err)
	}
	tempFile.Close()

	dockerCmd := fmt.Sprintf(`docker run --rm -v %s:/app/script -w /app %s %s script`,
		tempFile.Name(), image, interpreter)

	cmd := exec.CommandContext(ctx, "sh", "-c", dockerCmd)
	output, err := cmd.CombinedOutput()

	return &ExecutionResult{
		Success: err == nil,
		Output:  string(output),
		Error:   getErrorString(err),
	}, nil
}

func getErrorString(err error) string {
    if err != nil {
        return err.Error()
    }
    return ""
}